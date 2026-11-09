<?php
declare(strict_types=1);

use App\Service\AssistantPlatformHost;
use PHPUnit\Framework\TestCase;

final class AssistantPlatformHostStatePolicyTest extends TestCase
{
    public function testCurrentProcessIdentityMustMatchExactly(): void
    {
        $state = ['schema' => 'ezs.assistant.platform-host.v1', 'pid' => 68704, 'created' => '20261109210914.261963+060'];
        self::assertTrue(AssistantPlatformHost::priorStateIsLive($state, '20261109210914.261963+060'));
        self::assertFalse(AssistantPlatformHost::priorStateIsLive($state, null));
        self::assertFalse(AssistantPlatformHost::priorStateIsLive($state, 'different-process-creation'));
    }

    public function testInvalidStateNeverAttestsLiveProcess(): void
    {
        self::assertFalse(AssistantPlatformHost::priorStateIsLive(['pid' => 68704], 'date'));
        self::assertFalse(AssistantPlatformHost::priorStateIsLive(['schema' => 'ezs.assistant.platform-host.v1', 'pid' => '68704', 'created' => 'date'], 'date'));
    }
}
