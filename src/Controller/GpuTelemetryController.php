<?php
declare(strict_types=1);

namespace App\Controller;

use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\Routing\Attribute\Route;

final class GpuTelemetryController
{
    #[Route('/assistant/gpu/telemetry', name: 'assistant_gpu_telemetry', methods: ['GET'])]
    public function telemetry(): JsonResponse
    {
        // Host telemetry is shared read-only. Never grant the Web container GPU access.
        $path = getenv('EZSTUDIO_GPU_TELEMETRY_FILE');
        if (!is_string($path) || $path !== '/run/ezstudio-gpu/telemetry.json' || !is_file($path)) {
            return $this->unavailable('gpu_telemetry_source_missing');
        }
        $raw = @file_get_contents($path, false, null, 0, 4096);
        $data = is_string($raw) ? json_decode($raw, true) : null;
        if (!is_array($data) || ($data['available'] ?? null) !== true ||
            !is_numeric($data['timestamp_ms'] ?? null) ||
            !is_array($data['gpu'] ?? null)) {
            return $this->unavailable('gpu_telemetry_invalid');
        }
        $timestamp = (int) $data['timestamp_ms'];
        $now = (int) round(microtime(true) * 1000);
        if ($timestamp > $now + 2000 || $timestamp < $now - 12000) {
            return $this->unavailable('gpu_telemetry_stale');
        }
        $gpu = $data['gpu'];
        foreach (['name', 'utilization_percent', 'memory_used_mib', 'memory_total_mib',
            'memory_percent', 'temperature_c', 'power_w', 'power_limit_w',
            'power_percent', 'sm_clock_mhz', 'pstate'] as $key) {
            if (!array_key_exists($key, $gpu)) {
                return $this->unavailable('gpu_telemetry_invalid');
            }
        }
        if (!is_string($gpu['name']) || !is_string($gpu['pstate'])) {
            return $this->unavailable('gpu_telemetry_invalid');
        }
        foreach (['utilization_percent','memory_used_mib','memory_total_mib','memory_percent',
            'temperature_c','power_w','power_limit_w','power_percent','sm_clock_mhz'] as $key) {
            if ($gpu[$key] !== null && (!is_numeric($gpu[$key]) || !is_finite((float) $gpu[$key]))) {
                return $this->unavailable('gpu_telemetry_invalid');
            }
        }
        return new JsonResponse(['available' => true, 'timestamp_ms' => $timestamp, 'gpu' => $gpu]);
    }

    private function unavailable(string $reason): JsonResponse
    {
        return new JsonResponse([
            'available' => false,
            'error' => $reason,
            'timestamp_ms' => (int) round(microtime(true) * 1000),
        ], 503);
    }
}
