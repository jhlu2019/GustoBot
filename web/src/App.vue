<template>
  <div class="app-shell">
    <LandingPage @start-chat="openChat" />
    <ChatWidget ref="chatWidgetRef" />
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import LandingPage from "./components/LandingPage.vue";
import ChatWidget from "./components/ChatWidget.vue";

const chatWidgetRef = ref<InstanceType<typeof ChatWidget> | null>(null);

function openChat() {
  chatWidgetRef.value?.openChat();
}
</script>

<style scoped>
.app-shell {
  min-height: 100vh;
}
</style>
