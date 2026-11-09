<?php
declare(strict_types=1);

use App\Service\AssistantLlamaLifecycle;
use PHPUnit\Framework\TestCase;

final class AssistantLlamaStopIdentity165Test extends TestCase
{
    private const PATH = 'H:\\EZStudioLab_assistant\\runtime\\ai\\bin\\llama-server.exe';
    private const ARGS = '"H:\\EZStudioLab_assistant\\runtime\\ai\\bin\\llama-server.exe" -m "H:\\EZStudioLab_assistant\\runtime\\models-cache\\assistant\\bench\\qwen.gguf" -dev Vulkan1 -ngl 99 -c 4096 --host 127.0.0.1 --port 8720';

    public function testAcceptsExactlyOwnedLlama(): void
    {
        self::assertTrue(AssistantLlamaLifecycle::isOwnedStopTarget(self::PATH, self::ARGS));
    }

    public function testRejectsForeignPathsAndPorts(): void
    {
        self::assertFalse(AssistantLlamaLifecycle::isOwnedStopTarget('C:\\Other\\llama-server.exe', self::ARGS));
        self::assertFalse(AssistantLlamaLifecycle::isOwnedStopTarget(self::PATH, str_replace('--port 8720','--port 9999',self::ARGS)));
        self::assertFalse(AssistantLlamaLifecycle::isOwnedStopTarget(self::PATH, str_replace('-dev Vulkan1','-dev CPU',self::ARGS)));
        self::assertFalse(AssistantLlamaLifecycle::isOwnedStopTarget(self::PATH, str_replace('runtime\\models-cache\\assistant\\','other\\',self::ARGS)));
        self::assertFalse(AssistantLlamaLifecycle::isOwnedStopTarget(self::PATH, ''));
    }
}
