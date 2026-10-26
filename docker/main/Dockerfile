# MAIN-only isolated Symfony smoke target. No Qwen, GPU, workers or LAB credentials.
FROM php:8.4-cli-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends libicu-dev libzip-dev unzip git python3-minimal ca-certificates \
    && docker-php-ext-install intl zip opcache \
    && rm -rf /var/lib/apt/lists/*
COPY --from=composer:2 /usr/bin/composer /usr/local/bin/composer
WORKDIR /opt/ezstudio-assistant
COPY composer.json composer.lock* ./
RUN composer install --no-dev --no-interaction --no-progress --prefer-dist --no-scripts --optimize-autoloader
COPY . .
ENV APP_ENV=prod APP_DEBUG=0 EZSTUDIOLAB_ASSISTANT_PYTHON=python3
EXPOSE 8713
CMD ["php", "-S", "0.0.0.0:8713", "-t", "public", "public/index.php"]
