<?php
namespace App\Controller;
use Psr\Log\LoggerInterface;
use Symfony\Bundle\FrameworkBundle\Controller\AbstractController;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\Process\Process;
use Symfony\Component\Routing\Attribute\Route;
final class DashboardController extends AbstractController {
    public function __construct(private readonly LoggerInterface $logger) {}
    #[Route('/', name: 'assistant_dashboard', methods: ['GET'])]
    public function index(): Response {
        $root = dirname(__DIR__, 2);
        return $this->render('dashboard/index.html.twig', ['version' => trim((string) @file_get_contents($root.'/VERSION'))]);
    }
    #[Route('/api/health', name: 'assistant_health', methods: ['GET'])]
    public function health(): JsonResponse {
        return $this->json(['ok'=>true,'service'=>'EZStudioLab Assistant','tier'=>'web','database'=>false,'persistence_owner'=>'LAB']);
    }
    #[Route('/api/status', name: 'assistant_status', methods: ['GET'])]
    public function status(): JsonResponse {
        $root = dirname(__DIR__, 2);
        $python = $_ENV['EZSTUDIOLAB_ASSISTANT_PYTHON'] ?? $_SERVER['EZSTUDIOLAB_ASSISTANT_PYTHON'] ?? 'python';
        $process = new Process([$python, $root.'/app/web_status.py']);
        $process->setTimeout(8.0);
        try {
            $process->run();
            if (!$process->isSuccessful()) throw new \RuntimeException(trim($process->getErrorOutput()) ?: 'python_status_failed');
            $payload = json_decode($process->getOutput(), true, flags: JSON_THROW_ON_ERROR);
            if (!is_array($payload)) throw new \RuntimeException('python_status_not_object');
            return $this->json($payload);
        } catch (\Throwable $e) {
            $this->logger->error('Assistant Python status failed', ['exception'=>$e]);
            return $this->json(['ok'=>false,'state'=>'ERROR','error'=>$e->getMessage()], 503);
        }
    }
    #[Route('/api/profile/direct-research', name: 'assistant_profile_direct_research', methods: ['POST'])]
    public function directResearch(\Symfony\Component\HttpFoundation\Request $request): JsonResponse {
        $data = json_decode($request->getContent(), true);
        if (!is_array($data)) return $this->json(['ok'=>false,'error'=>'invalid_json'],400);
        $title = trim((string) ($data['title'] ?? ''));
        $artist = trim((string) ($data['artist'] ?? ''));
        $items = $data['items'] ?? [];
        if ($title === '' || $artist === '' || mb_strlen($title)>180 || mb_strlen($artist)>180
            || !is_array($items) || count($items)<1 || count($items)>9) {
            return $this->json(['ok'=>false,'error'=>'invalid_research_request'],400);
        }
        $root = dirname(__DIR__, 2);
        $python = $_ENV['EZSTUDIOLAB_ASSISTANT_PYTHON'] ?? $_SERVER['EZSTUDIOLAB_ASSISTANT_PYTHON'] ?? 'python';
        $process = new Process([$python, $root.'/runtime/profile_direct_research.py'], $root,
            null, json_encode($data, JSON_UNESCAPED_UNICODE | JSON_THROW_ON_ERROR));
        $process->setTimeout(180.0);
        try {
            $process->run();
            $result = json_decode($process->getOutput(), true, flags: JSON_THROW_ON_ERROR);
            if (!is_array($result)) throw new \RuntimeException('invalid_python_response');
            if (!$process->isSuccessful()) {
                return $this->json(['ok'=>false,'error'=>$result['error'] ?? 'research_failed',
                    'reason'=>$result['reason'] ?? 'Recherche indisponible'],503);
            }
            return $this->json($result);
        } catch (\Throwable $e) {
            $this->logger->error('PROFILE direct research failed', ['exception'=>$e]);
            return $this->json(['ok'=>false,'error'=>'research_execution_failed',
                'reason'=>get_class($e)],503);
        }
    }

}
