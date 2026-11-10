<?php
declare(strict_types=1);

require_once dirname(__DIR__).'/src/Service/AssistantPlatformHost.php';

use App\Service\AssistantPlatformHost;

function check173(bool $condition, string $label): void
{
    if (!$condition) {
        throw new RuntimeException('ATTEST_173_FAILED_'.$label);
    }
}

$attempts = 0;
$waits = 0;
$identity = AssistantPlatformHost::attestStartedWebProcess(
    static fn (): bool => true,
    static function () use (&$attempts): ?string {
        ++$attempts;
        return $attempts === 3 ? '20261110103000.000000+060' : null;
    },
    static function () use (&$waits): void { ++$waits; },
    5
);
check173($identity === '20261110103000.000000+060', 'TRANSIENT_IDENTITY');
check173($attempts === 3 && $waits === 2, 'BOUNDED_RETRY');

$attempts = 0;
$identity = AssistantPlatformHost::attestStartedWebProcess(
    static fn (): bool => true,
    static function () use (&$attempts): ?string { ++$attempts; return null; },
    static function (): void {},
    4
);
check173($identity === null && $attempts === 4, 'NO_FALSE_POSITIVE');

$attempts = 0;
$identity = AssistantPlatformHost::attestStartedWebProcess(
    static fn (): bool => false,
    static function () use (&$attempts): ?string { ++$attempts; return 'untrusted'; },
    static function (): void {},
    3
);
check173($identity === null && $attempts === 0, 'EXIT_BEFORE_ATTESTATION');

$runningChecks = 0;
$identity = AssistantPlatformHost::attestStartedWebProcess(
    static function () use (&$runningChecks): bool { return ++$runningChecks === 1; },
    static fn (): ?string => 'creation-date',
    static function (): void {},
    3
);
check173($identity === null, 'PROCESS_EXIT_AFTER_WMI');

$identity = AssistantPlatformHost::attestStartedWebProcess(
    static fn (): bool => true,
    static fn (): ?string => '',
    static function (): void {},
    2
);
check173($identity === null, 'EMPTY_IDENTITY_REJECTED');

$rejected = false;
try {
    AssistantPlatformHost::attestStartedWebProcess(
        static fn (): bool => true,
        static fn (): ?string => 'created',
        static function (): void {},
        22
    );
} catch (InvalidArgumentException $e) {
    $rejected = true;
}
check173($rejected, 'UNBOUNDED_RETRY_REJECTED');

echo "ATTEST_173_TESTS_OK=6\n";
