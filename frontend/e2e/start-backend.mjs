// Arranca el backend para los tests E2E sobre un catálogo NUEVO en frontend/.e2e/data.
//
// Cada ejecución empieza de cero: importa el catálogo con el mismo importador que usa la suite de pytest
// (con portadas e informe redirigidos, para no reescribir frontend/public/covers), crea un administrador de
// prueba y levanta uvicorn en el puerto 8300. No toca backend/data ni los servidores de desarrollo (3000/8000).

import { spawn, spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..");
const backend = path.join(root, "backend");
const e2eDir = path.join(root, "frontend", ".e2e");
const data = path.join(e2eDir, "data");

const python =
  [path.join(backend, ".venv", "Scripts", "python.exe"), path.join(backend, ".venv", "bin", "python")].find((p) =>
    fs.existsSync(p),
  ) ?? "python";

fs.rmSync(e2eDir, { recursive: true, force: true });
fs.mkdirSync(data, { recursive: true });

const env = {
  ...process.env,
  DATA_DIR: data,
  PAYMENT_DELAY_SECONDS: "0.05", // el pago simulado tarda 0,8 s en desarrollo; en tests basta con una pausa mínima
  FRONTEND_ORIGIN: "http://localhost:3300",
  PYTHONIOENCODING: "utf-8",
};

function run(args, options = {}) {
  const result = spawnSync(python, args, { cwd: backend, env, encoding: "utf-8", ...options });
  if (result.status !== 0) {
    console.error(`Falló: ${python} ${args.join(" ")}\n${result.stdout}\n${result.stderr}`);
    process.exit(1);
  }
}

// 1) Catálogo semilla determinista (stock 3-30, descuentos, 37 libros, reseñas de muestra).
run([
  "-c",
  [
    "import sys; sys.path.insert(0, '.')",
    "from pathlib import Path",
    "import scripts.import_legacy as importer",
    "data = Path(sys.argv[1])",
    "importer.COVERS_DIR = data / 'covers'",
    "importer.REPORT_PATH = data / 'import_report.md'",
    "raise SystemExit(importer.main(force=True))",
  ].join("\n"),
  data,
]);

// 2) Administrador de prueba (la contraseña entra por stdin, como en el uso real).
run(
  ["-m", "scripts.seed_admin", "--password-stdin", "--email", "admin.e2e@correo.com", "--first-name", "Irene", "--last-name", "Admin"],
  { input: "clave-admin-1\n" },
);

// 3) El servidor. Si Playwright nos termina, se termina también.
const server = spawn(python, ["-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8300"], {
  cwd: backend,
  env,
  stdio: "inherit",
});
for (const signal of ["SIGINT", "SIGTERM"]) process.on(signal, () => server.kill());
server.on("exit", (code) => process.exit(code ?? 0));
