# Texlive Server

Serving TexLive Files in an On-Demand Manner. 

This is an adaptation of the [SwiftLaTeX Texlive 2 server](https://github.com/SwiftLaTeX/Texlive-Ondemand) made deployable with Cloudflare Tunnel.

## Deployment with Cloudflare Tunnel

1. Create a Cloudflare account and add your domain.
2. Get the Global API token from Cloudflare.
3. Copy the envfile to `.env` and fill in the required values including the `CLOUDFLARE_API_KEY` and `HOST_DOMAIN` (the link to your cloudflared domain or sub-domain).
4. Run the following command to build the docker file:
   ```bash
   docker compose -f docker-compose.cloudflare.yml build
   ```
5. Run the following command to start the cloudflare deployment:
   ```bash
   docker compose -f docker-compose.cloudflare.yml up -d
   chmod +x ./scripts/run_texlive_cloudflare_tunnel.sh
   source ./.env && ./scripts/run_texlive_cloudflare_tunnel.sh "${CLOUDFLARE_API_KEY}" "${HOST_DOMAIN}" "${PORT}"
   ```
   **NOTE** You can stop the deployment with `docker compose -f docker-compose.cloudflare.yml down` command.

6. On the first usage, you will be directed to the Cloudflare login page. After logging in, you will have to authorize the domain you specified in the `.env` file `HOST_DOMAIN`.
7. After the authorization, you will be redirected to the Texlive app. You can now use the app with your custom domain.
