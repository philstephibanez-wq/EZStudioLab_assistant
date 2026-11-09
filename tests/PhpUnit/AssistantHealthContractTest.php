<?php
declare(strict_types=1);

use App\Service\AssistantLlamaLifecycle;
use PHPUnit\Framework\TestCase;

final class AssistantHealthContractTest extends TestCase
{
    public function testHardAndSoftProbesRemainReadOnly(): void
    {
        $root = dirname(__DIR__, 2);
        $script = (string) file_get_contents($root.'/scripts/ai-health-pings.ps1');
        self::assertStringContainsString("classification='HARD'", $script);
        self::assertStringContainsString("classification='SOFT'", $script);
        self::assertStringContainsString('127.0.0.1:8720/health', $script);
        self::assertStringContainsString('127.0.0.1:8713/api/inference/status', $script);
        foreach (['Start-ScheduledTask','Stop-ScheduledTask','Start-Service','Stop-Service','Stop-Process'] as $forbidden) {
            self::assertStringNotContainsString($forbidden, $script);
        }
    }

    public function testCanonicalSymfonyConsoleIsInstalled(): void
    {
        $root = dirname(__DIR__, 2);
        self::assertFileExists($root.'/bin/console');
        $manifest = json_decode((string) file_get_contents($root.'/composer.json'), true, flags: JSON_THROW_ON_ERROR);
        self::assertNotEmpty($manifest['require']['symfony/console'] ?? null);
        self::assertStringContainsString('autoload_runtime.php', (string) file_get_contents($root.'/bin/console'));
    }

    public function testPhpEventOwnsGpuAndNoPeriodicSupervisor(): void
    {
        $root = dirname(__DIR__, 2);
        $php = (string) file_get_contents($root.'/src/Service/AssistantLlamaLifecycle.php');
        self::assertStringContainsString('EZS_FrankenPHP', $php);
        self::assertStringContainsString('Vulkan1', $php);
        self::assertStringContainsString('WScript.Shell', $php);
        self::assertStringContainsString('NATIVE_START_REQUESTED_WITHOUT_CONSOLE', $php);
        self::assertStringContainsString('FRANKENPHP_STOP_LLAMA_TERMINATED_COUNT', $php);
        self::assertStringNotContainsString('Start-ScheduledTask', $php);
        self::assertStringNotContainsString('wscript.exe', $php);
        self::assertSame('STOP', AssistantLlamaLifecycle::decide('Stopped', true));
        self::assertSame('STOP', AssistantLlamaLifecycle::decide('Stopped', false));
        self::assertSame('START', AssistantLlamaLifecycle::decide('Running', true));
        self::assertSame('SKIP', AssistantLlamaLifecycle::decide('Running', false));
        self::assertSame('SKIP', AssistantLlamaLifecycle::decide('Stop Pending', true));
    }
}
