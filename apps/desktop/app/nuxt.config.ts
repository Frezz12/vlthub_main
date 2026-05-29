export default defineNuxtConfig({
  devtools: { enabled: true },
  ssr: process.env.NUXT_BUILD_TARGET === "static" ? false : true,

  modules: ["@pinia/nuxt", "@nuxtjs/tailwindcss"],

  components: [{ path: "~/components", pathPrefix: false }],

  srcDir: ".",

  css: ["~/assets/css/main.css"],

  app: {
    head: {
      title: "VLTHub",
      meta: [
        { name: "viewport", content: "width=device-width, initial-scale=1" },
        { name: "color-scheme", content: "light dark" },
      ],
      link: [{ rel: "icon", type: "image/svg+xml", href: "/favicon.svg" }],
    },
  },

  nitro: {
    devProxy: {
      "/api": process.env.NUXT_PUBLIC_API_BASE_URL || "https://vlthub.ru",
    },
  },

  vite: {
    define: {
      __API_BASE_URL__: JSON.stringify(
        process.env.NUXT_PUBLIC_API_BASE_URL || "",
      ),
    },
    server: {
      proxy: {
        "/api": {
          target:
            process.env.NUXT_PUBLIC_API_BASE_URL || "https://vlthub.ru",
          changeOrigin: true,
        },
        "/uploads": {
          target:
            process.env.NUXT_PUBLIC_API_BASE_URL || "https://vlthub.ru",
          changeOrigin: true,
        },
        "/downloads": {
          target:
            process.env.NUXT_PUBLIC_API_BASE_URL || "https://vlthub.ru",
          changeOrigin: true,
        },
      },
    },
  },

  runtimeConfig: {
    public: {
      apiBaseUrl:
        process.env.NUXT_PUBLIC_API_BASE_URL || "https://vlthub.ru",
    },
  },

  compatibilityDate: "2026-05-25",
});
