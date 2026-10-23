<?php

declare(strict_types=1);

namespace App\Controller;

use Symfony\Bundle\FrameworkBundle\Controller\AbstractController;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\Process\Process;
use Symfony\Component\Routing\Attribute\Route;

final class ProfileVerificationController extends AbstractController
{
    #[Route('/api/profile/verify', name: 'assistant_profile_verify_push', methods: ['POST'])]
    public function verify(Request $request): JsonResponse
    {
        $token = (string) $request->headers->get('X-EZScore-Analysis-Token', '');
        if ($token === '') {
            return $this->json(['error' => 'unauthorized'], 401);
        }
        try {
            $data = $request->toArray();
            if (array_key_exists('_auth_token', $data)) {
                return $this->json(['error' => 'reserved_field'], 422);
            }
            if (($data['expertise_type'] ?? null) !== 'profile') {
                return $this->json(['error' => 'expertise_type_not_implemented'], 422);
            }
            $data['_auth_token'] = $token;
            $root = dirname(__DIR__, 2);
            $python = $_ENV['EZSTUDIOLAB_ASSISTANT_PYTHON']
                ?? $_SERVER['EZSTUDIOLAB_ASSISTANT_PYTHON'] ?? 'python';
            $process = new Process([$python, $root.'/runtime/profile_verify_push.py'], $root);
            $process->setInput(json_encode($data, JSON_THROW_ON_ERROR | JSON_UNESCAPED_UNICODE));
            $process->setTimeout(900);
            $process->run();
            $result = json_decode($process->getOutput(), true, flags: JSON_THROW_ON_ERROR);
            if (!$process->isSuccessful()) {
                return $this->json(['error' => $result['error'] ?? 'verification_failed'], 
                    ($result['error'] ?? '') === 'unauthorized' ? 401 : 422);
            }
            return $this->json($result);
        } catch (\Throwable $e) {
            return $this->json(['error' => 'verification_processing_failed'], 503);
        }
    }
}
