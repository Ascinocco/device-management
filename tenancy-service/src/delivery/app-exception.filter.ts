import {
  ArgumentsHost,
  Catch,
  ExceptionFilter,
  HttpStatus,
} from "@nestjs/common";
import { Response } from "express";
import { ZodError } from "zod";

import { NotFoundError, ValidationError } from "../app/contracts";

@Catch()
export class AppExceptionFilter implements ExceptionFilter {
  catch(exception: unknown, host: ArgumentsHost): void {
    const ctx = host.switchToHttp();
    const response = ctx.getResponse<Response>();

    if (exception instanceof ZodError) {
      response.status(HttpStatus.BAD_REQUEST).json({
        error: "validation_error",
        message: "Invalid request body",
        details: exception.errors,
      });
      return;
    }

    if (exception instanceof ValidationError) {
      response.status(HttpStatus.BAD_REQUEST).json({
        error: "validation_error",
        message: exception.message,
      });
      return;
    }

    if (exception instanceof NotFoundError) {
      response.status(HttpStatus.NOT_FOUND).json({
        error: "not_found",
        message: exception.message,
      });
      return;
    }

    console.error("[tenancy] unhandled exception:", exception);
    response.status(HttpStatus.INTERNAL_SERVER_ERROR).json({
      error: "internal_error",
      message: "Internal server error",
    });
  }
}
