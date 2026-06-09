<template>
  <div class="animated-background">
    <div v-for="i in 30" :key="i" class="circle" :style="getCircleStyle(i)" />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

function getRandom(min: number, max: number) {
  return Math.random() * (max - min) + min
}

function getCircleStyle(index: number) {
  const size = getRandom(40, 200) // Slightly larger circles
  const duration = getRandom(15, 30)
  const delay = getRandom(0, 10)
  const left = getRandom(0, 100)
  const top = getRandom(0, 100)

  return {
    width: `${size}px`,
    height: `${size}px`,
    left: `${left}%`,
    top: `${top}%`,
    animationDuration: `${duration}s`,
    animationDelay: `${delay}s`,
    opacity: getRandom(0.1, 0.3),
    backgroundColor: `hsl(${getRandom(180, 260)}, ${getRandom(60, 80)}%, ${getRandom(70, 90)}%)`, // Brighter, more varied blueish hues
  }
}
</script>

<style scoped>
.animated-background {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  z-index: -1;
  /* Ensure it has a background for contrast, though it should be handled by body */
  background-color: var(--color-surface);
}

.circle {
  position: absolute;
  border-radius: 50%;
  pointer-events: none;
  animation: float 20s infinite ease-in-out;
}

@keyframes float {
  0% {
    transform: translateY(0) scale(1);
  }
  50% {
    transform: translateY(-50px) scale(1.05);
  }
  100% {
    transform: translateY(0) scale(1);
  }
}
</style>
