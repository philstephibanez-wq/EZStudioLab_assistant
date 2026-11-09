<?php
declare(strict_types=1);

namespace App\Service;

/** One-shot service owner: runs the existing FrankenPHP command until it exits.
 *  Not a health monitor, watchdog, restart mechanism or supervisor of websites.
 */
final class AssistantPlatformHost
{
    private const ROOT = 'H:\\EZStudioLab_assistant';
    private const WEB_EXE = 'H:\\FRANKENPHP\\bin\\frankenphp.exe';
    private const WEB_CFG = 'H:\\EZS_orchestrator\\config\\frankenphp\\Caddyfile.platform.unified';
    private const STATE = self::ROOT.'\\runtime\\state\\platform-host-163.json';
    private const LOG = self::ROOT.'\\runtime\\state\\platform-host-163.log';


    private int $webPid = 0;
    private bool $stopRequested = false;

    public function __construct(private readonly AssistantLlamaLifecycle $llama) {}

    /** WinSW 2.12 forwards Ctrl+C to the PHP console process on SCM STOP.
     *  Signal the verified FrankenPHP child process group; never use a force kill.
     */
    public function onWindowsCtrl(int $event): bool
    {
        if ($this->stopRequested) return true;
        $this->stopRequested = true;
        $this->log('WINSW_STOP_SIGNAL='.$event.' WEB_PID='.$this->webPid);
        if ($this->webPid < 1 || $this->identity($this->webPid) === null) {
            $this->log('STOP_SIGNAL_WEB_NOT_ATTESTED');
            return true;
        }
        // CTRL+BREAK can target the child CREATE_NEW_PROCESS_GROUP process.
        $ok = sapi_windows_generate_ctrl_event(PHP_WINDOWS_EVENT_CTRL_BREAK, $this->webPid);
        $this->log('WEB_CTRL_BREAK_SENT='.($ok ? 'YES' : 'NO'));
        return true;
    }

    public static function priorStateIsLive(array $state, ?string $currentWebCreation): bool
    {
        return ($state['schema'] ?? null) === 'ezs.assistant.platform-host.v1'
            && is_int($state['pid'] ?? null) && ($state['pid'] ?? 0) > 0
            && is_string($state['created'] ?? null)
            && $currentWebCreation !== null
            && hash_equals($state['created'], $currentWebCreation);
    }

    private function recoverStaleState(): bool
    {
        if (!is_file(self::STATE)) return true;
        $state = $this->readState();
        if ($state === null) {
            $this->log('START_REFUSED_INVALID_STATE');
            return false;
        }
        try {
            $current = $this->identity($state['pid']);
            if (self::priorStateIsLive($state, $current)) {
                $this->log('START_REFUSED_LIVE_WEB_STATE pid='.$state['pid']);
                return false;
            }
            // Fail closed if any FrankenPHP server is still running.
            $wmi = new \COM('winmgmts://');
            foreach ($wmi->ExecQuery("SELECT ProcessId, ExecutablePath FROM Win32_Process WHERE Name='frankenphp.exe'") as $p) {
                if (strcasecmp(str_replace('/', '\\', (string)$p->ExecutablePath), self::WEB_EXE) === 0) {
                    $this->log('START_REFUSED_FRANKENPHP_PROCESS_STILL_ACTIVE pid='.$p->ProcessId);
                    return false;
                }
            }
        } catch (\Throwable $e) {
            $this->log('START_REFUSED_STATE_ATTESTATION_FAILED '.$e->getMessage());
            return false;
        }
        $archive = self::STATE.'.stale.'.gmdate('YmdHis').'.'.getmypid().'.json';
        if (!@rename(self::STATE, $archive)) {
            $this->log('START_REFUSED_STALE_STATE_ARCHIVE_FAILED');
            return false;
        }
        $this->log('STALE_STATE_ARCHIVED '.basename($archive));
        return true;
    }

    public function start(): int
    {
        if (!is_file(self::WEB_EXE) || !is_file(self::WEB_CFG)) {
            $this->log('START_REFUSED_MISSING_WEB_FILES');
            return 3;
        }
        if (!$this->recoverStaleState()) return 3;
        $dir = dirname(self::STATE);
        if (!is_dir($dir) && !mkdir($dir, 0770, true) && !is_dir($dir)) return 3;
        if (PHP_OS_FAMILY !== 'Windows' || !function_exists('sapi_windows_set_ctrl_handler') ||
            !function_exists('sapi_windows_generate_ctrl_event') ||
            !defined('PHP_WINDOWS_EVENT_CTRL_BREAK')) {
            $this->log('WINDOWS_CTRL_HANDLER_UNAVAILABLE');
            return 3;
        }
        if (!sapi_windows_set_ctrl_handler([$this, 'onWindowsCtrl'])) {
            $this->log('WINDOWS_CTRL_HANDLER_INSTALL_FAILED');
            return 3;
        }
        $stdout = $dir.'\\frankenphp-host-stdout.log';
        $stderr = $dir.'\\frankenphp-host-stderr.log';
        $cmd = [self::WEB_EXE, 'run', '--config', self::WEB_CFG, '--adapter', 'caddyfile'];
        // The Windows service is non-interactive. No shell and no additional console.
        $proc = @proc_open($cmd, [0 => ['pipe','r'], 1 => ['file',$stdout,'a'], 2 => ['file',$stderr,'a']], $pipes, 'H:\\EZS_orchestrator', null, ['bypass_shell'=>true,'create_process_group'=>true]);
        if (!is_resource($proc)) {
            $this->log('WEB_PROCESS_LAUNCH_FAILED');
            return 3;
        }
        fclose($pipes[0]);
        $status = proc_get_status($proc);
        $pid = (int) ($status['pid'] ?? 0);
        if ($pid < 1 || !($status['running'] ?? false)) {
            $this->log('WEB_PROCESS_EXITED_EARLY');
            proc_close($proc);
            return 3;
        }
        $this->webPid = $pid;
        $identity = $this->identity($pid);
        if ($identity === null) {
            $this->log('WEB_PROCESS_IDENTITY_NOT_ATTESTED pid='.$pid);
            // Refuse to kill a process with unverified identity.
            proc_close($proc);
            return 3;
        }
        $json = json_encode(['schema'=>'ezs.assistant.platform-host.v1','pid'=>$pid,'created'=>$identity], JSON_THROW_ON_ERROR);
        $tmp = self::STATE.'.'.getmypid().'.tmp';
        if (file_put_contents($tmp,$json,LOCK_EX) === false || !rename($tmp,self::STATE)) {
            $this->log('STATE_WRITE_FAILED');
            @unlink($tmp);
            // Refuse to kill a process with unverified identity.
            proc_close($proc);
            return 3;
        }
        $this->log('WEB_STARTED pid='.$pid);
        // Web and the Assistant health endpoint must be up before invoking Llama.
        // This wait happens ONCE at startup. No periodic monitoring/restarts.
        $ready = false;
        for ($i=0; $i<40; ++$i) {
            $s = proc_get_status($proc);
            if (!$s['running']) break;
            if ($this->assistantWebReady()) { $ready = true; break; }
            sleep(1);
        }
        if ($ready && !$this->stopRequested) {
            // WinSW should have marked the PHP host service Running by now.
            $result = $this->llama->run();
            $this->log('LLAMA_START_RETURN_CODE='.$result);
        } else {
            $this->log('ASSISTANT_WEB_NOT_READY_LLAMA_NOT_STARTED');
        }
        // Never block in proc_close while WinSW is delivering CTRL+C. On Windows,
        // the registered PHP console handler must be given VM execution points.
        // This is a lifetime wait ONLY: no service health polling or restarts.
        // A short wait also lets the signal handler execute promptly during STOP.
        $exit = -1;
        do {
            $status = proc_get_status($proc);
            if (!$status['running']) {
                $exit = (int) $status['exitcode'];
                break;
            }
            usleep(200000);
        } while (true);
        proc_close($proc); // No longer a blocking process wait.
        $plannedStop = $this->stopRequested;
        $this->log('WEB_EXIT_CODE='.$exit.' PLANNED_STOP='.($plannedStop ? 'YES' : 'NO'));
        $llamaStop = $this->llama->stopOwned();
        $this->log('LLAMA_STOP_RETURN_CODE='.$llamaStop);
        // Only remove state that still belongs to our web process.
        $recorded = $this->readState();
        if ($recorded !== null && $recorded['pid'] === $pid && $recorded['created'] === $identity) {
            if (!@unlink(self::STATE)) $this->log('STATE_CLEANUP_FAILED');
            else $this->log('STATE_CLEANED_AFTER_WEB_EXIT');
        } else {
            $this->log('STATE_CLEANUP_REFUSED_IDENTITY_CHANGED');
        }
        return ($llamaStop === 0 && ($plannedStop || $exit === 0)) ? 0 : 2;
    }

    private function assistantWebReady(): bool
    {
        $context = stream_context_create(['http'=>['timeout'=>1]]);
        $body = @file_get_contents('http://127.0.0.1:8713/api/health',false,$context);
        $json = is_string($body) ? json_decode($body,true) : null;
        return is_array($json) && ($json['ok']??false)===true && ($json['service']??'')==='EZStudioLab Assistant';
    }

    private function readState(): ?array
    {
        $raw = @file_get_contents(self::STATE);
        $state = is_string($raw) ? json_decode($raw,true) : null;
        return is_array($state) && ($state['schema']??'')==='ezs.assistant.platform-host.v1' &&
            is_int($state['pid']??null) && is_string($state['created']??null) ? $state : null;
    }

    private function identity(int $pid): ?string
    {
        if ($pid < 1) return null;
        $wmi = new \COM('winmgmts://');
        foreach ($wmi->ExecQuery('SELECT ExecutablePath,CommandLine,CreationDate FROM Win32_Process WHERE ProcessId='.$pid) as $process) {
            if (strcasecmp(str_replace('/','\\',(string)$process->ExecutablePath),self::WEB_EXE) !== 0 ||
                stripos((string)$process->CommandLine,self::WEB_CFG) === false) return null;
            return (string)$process->CreationDate;
        }
        return null;
    }

    private function log(string $message): void
    {
        $dir=dirname(self::LOG);
        if (!is_dir($dir)) @mkdir($dir,0770,true);
        @file_put_contents(self::LOG,gmdate('c').' '.$message.PHP_EOL,FILE_APPEND|LOCK_EX);
    }
}
