import { createApp } from "vue";
import { createPinia } from "pinia";
import {
  Chart as ChartJS,
  LineElement,
  PointElement,
  LineController,
  CategoryScale,
  LinearScale,
  Tooltip,
  Legend,
  Filler,
} from "chart.js";

import "./assets/main.css";
import App from "./App.vue";
import router from "./router";

ChartJS.register(
  LineElement,
  PointElement,
  LineController,
  CategoryScale,
  LinearScale,
  Tooltip,
  Legend,
  Filler,
);

const app = createApp(App);

app.use(createPinia());
app.use(router);

app.mount("#app");
