import { Controller, Get, HttpStatus, Res } from "@nestjs/common";
import type { Response } from "express";

import { pool } from "../../infra/db/drizzle";

@Controller("internal")
export class HealthController {
  @Get("health")
  async health(@Res() res: Response) {
    try {
      await pool.query("SELECT 1");
      res.status(HttpStatus.OK).json({ ok: true });
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown error";
      res
        .status(HttpStatus.SERVICE_UNAVAILABLE)
        .json({ ok: false, error: message.slice(0, 256) });
    }
  }
}
