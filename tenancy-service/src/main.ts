import { NestFactory } from "@nestjs/core";

import { AppModule } from "./app.module";
import { settings } from "./app/settings";

async function bootstrap(): Promise<void> {
  const app = await NestFactory.create(AppModule);
  await app.listen(settings.port);
}

void bootstrap();
