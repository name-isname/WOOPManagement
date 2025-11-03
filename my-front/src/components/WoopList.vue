<script setup>
import { ref, onMounted } from 'vue'

const apiBase = 'http://localhost:8000'
const items = ref([])
const loading = ref(false)
const error = ref('')
const newTitle = ref('示例 WOOP')
const page = ref(1)
const size = ref(10)

async function fetchList() {
  loading.value = true
  error.value = ''
  try {
    const res = await fetch(`${apiBase}/woops/?page=${page.value}&size=${size.value}`)
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const data = await res.json()
    items.value = data.items || []
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

async function createItem() {
  loading.value = true
  error.value = ''
  try {
    const payload = { title: newTitle.value, description: '由前端示例创建', rank: 1 }
    const res = await fetch(`${apiBase}/woops/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
    if (!res.ok) {
      const txt = await res.text()
      throw new Error(`Create failed: ${res.status} ${txt}`)
    }
    newTitle.value = '示例 WOOP'
    await fetchList()
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

onMounted(fetchList)
</script>

<template>
  <section>
    <div class="mb-4 flex gap-2">
      <input v-model="newTitle" class="border p-2 flex-1" />
      <button @click="createItem" class="bg-blue-600 text-white px-4 py-2 rounded">创建</button>
      <button @click="fetchList" class="bg-gray-200 px-3 py-2 rounded">刷新</button>
    </div>

    <div v-if="loading" class="text-gray-500">加载中...</div>
    <div v-if="error" class="text-red-600">错误: {{ error }}</div>

    <ul class="space-y-3">
      <li v-for="it in items" :key="it.id" class="border p-3 rounded">
        <div class="font-semibold">{{ it.title }}</div>
        <div class="text-sm text-gray-600">{{ it.description }}</div>
  <!-- id and rank removed -->
      </li>
    </ul>

    <div class="mt-4 flex gap-2 items-center">
      <label>每页</label>
      <select v-model="size" @change="fetchList" class="border px-2 py-1">
        <option value="5">5</option>
        <option value="10">10</option>
        <option value="20">20</option>
      </select>
    </div>
  </section>
</template>

<style scoped>
input { min-width: 200px }
</style>