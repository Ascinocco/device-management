import { drizzle } from "drizzle-orm/node-postgres";
import { Pool } from "pg";

import { settings } from "../../app/settings";

export const pool = new Pool({
  connectionString: settings.databaseUrl,
});

export const db = drizzle(pool);
