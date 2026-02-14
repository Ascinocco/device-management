import { NestFactory } from "@nestjs/core";

import { AppModule } from "./app.module";
import { settings } from "./app/settings";
import { AppExceptionFilter } from "./delivery/app-exception.filter";

async function bootstrap(): Promise<void> {
  const app = await NestFactory.create(AppModule);
  app.useGlobalFilters(new AppExceptionFilter());
  await app.listen(settings.port);
}

void bootstrap();
