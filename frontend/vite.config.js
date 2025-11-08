import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    allowedHosts: [
      "localhost",
      "127.0.0.1",
      "ed876de0-495b-49bf-b9e5-2779d5526bd3-00-3834peuvckx8w.riker.replit.dev",
      "7148d403-d346-4078-9b6a-bacfd236762d-00-11f1bvhmjhlv9.picard.replit.dev", // 👈 added
    ],
    host: true,
    port: 5173,
  },
});
