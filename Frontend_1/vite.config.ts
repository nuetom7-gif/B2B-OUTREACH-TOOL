process.env["NAPI_RS_FORCE_WASI"] = "true";

const [{ defineConfig }, reactMod, tailwindMod, pathsMod, startMod] = await Promise.all([
  import("vite"),
  import("@vitejs/plugin-react"),
  import("@tailwindcss/vite"),
  import("vite-tsconfig-paths"),
  import("@tanstack/react-start/plugin/vite"),
]);

const react = reactMod.default;
const tailwindcss = tailwindMod.default;
const tsconfigPaths = pathsMod.default;
const { tanstackStart } = startMod;

export default defineConfig({
  plugins: [
    ...tanstackStart({
      server: {
        entry: "server",
      },
    }),
    react(),
    tailwindcss(),
    tsconfigPaths(),
  ],
});
