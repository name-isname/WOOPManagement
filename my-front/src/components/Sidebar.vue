<template>
  <aside class="sidebar" :class="{ expanded }" @mouseenter="expanded = true" @mouseleave="expanded = false">
    <!-- Brand -->
    <div class="brand" v-show="expanded">WOOP</div>
    <div class="rail-brand" v-show="!expanded">W</div>

    <!-- 账户登录模块已移除 -->

    <!-- Color palette -->
    <section class="block" v-show="expanded">
      <h4 class="block-title">主题色</h4>
      <div class="palette">
        <button v-for="c in colors" :key="c" :style="{background:c}"
                class="swatch" :aria-label="c" @click="selectColor(c)" />
      </div>
    </section>

    <!-- spacer to push footer to bottom -->
    <div style="flex:1"></div>

    <!-- Footer: Dark mode toggle button at bottom -->
    <div class="footer">
      <button class="mode-btn round" @click="toggleDark" :aria-label="dark ? '切换为明亮模式' : '切换为暗夜模式'" :title="dark ? '切换为明亮模式' : '切换为暗夜模式'">
        <span class="mode-ico">{{ dark ? '☀️' : '🌙' }}</span>
      </button>
    </div>

    <!-- Project details -->
    <section class="block" v-if="project" v-show="expanded">
      <h4 class="block-title">项目详情</h4>
      <div class="kv"><span class="k">名称</span><span class="v">{{ project.name }}</span></div>
      <div class="kv"><span class="k">愿望</span><span class="v">{{ project.wish }}</span></div>
      <div class="kv"><span class="k">障碍</span><span class="v">{{ project.obstacle }}</span></div>
      <div class="kv"><span class="k">计划</span><span class="v">{{ project.plan }}</span></div>
      <div class="kv"><span class="k">结果</span><span class="v">{{ project.outcome }}</span></div>
    </section>
  </aside>
</template>

<script setup>
import { ref, onMounted } from 'vue'

// 对外暴露：当前选中项目（可为空），以及选择主题色事件
const props = defineProps({ project: { type: Object, default: null } })
const emit = defineEmits(['theme-change'])

const colors = ['#3b82f6','#10b981','#f59e0b','#ef4444','#8b5cf6','#06b6d4']
const dark = ref(false)
const expanded = ref(false)

function selectColor(c){
  document.documentElement.style.setProperty('--brand', c)
  emit('theme-change', c)
}

function applyDark(){
  const el = document.documentElement
  if(dark.value){ el.classList.add('dark'); localStorage.setItem('theme','dark') }
  else { el.classList.remove('dark'); localStorage.setItem('theme','light') }
}

function toggleDark(){
  dark.value = !dark.value
  applyDark()
}

onMounted(()=>{
  const saved = localStorage.getItem('theme')
  if(saved === 'dark'){ dark.value = true; document.documentElement.classList.add('dark') }
})
</script>

<style scoped>
.sidebar{
  width: 56px;
  background: var(--sidebar-bg, #0f172a);
  color: #fff;
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 12px 8px;
  height: 100%;
  flex-shrink: 0;
  overflow-y: auto;
  transition: width .18s ease, padding .18s ease;
}
.sidebar.expanded{ width: 240px; padding: 16px 12px }
.brand{ font-weight: 700; letter-spacing: 1px; opacity:.9 }
.rail-brand{ font-weight: 800; font-size: 14px; opacity:.9; text-align:center }
.block{ background: rgba(255,255,255,.04); border: 1px solid rgba(255,255,255,.06); border-radius: 8px; padding: 12px }
.block + .block{ margin-top: 6px }
.block-title{ font-weight:600; font-size: 12px; opacity:.8; margin-bottom: 8px }
.palette{ display:flex; flex-wrap: wrap; gap:8px }
.swatch{ width: 24px; height: 24px; border-radius: 999px; border: 1px solid rgba(255,255,255,.3); cursor: pointer }
.kv{ display:flex; gap:8px; font-size:12px; padding:4px 0; border-bottom: 1px dashed rgba(255,255,255,.08) }
.kv:last-child{ border-bottom:none }
.k{ opacity:.7; min-width: 36px }
.v{ opacity:.95; word-break: break-all }
.btn{ background: var(--brand, #3b82f6); color:#fff; border:none; border-radius:6px; padding:6px 10px; cursor:pointer }
.btn:hover{ filter: brightness(1.05) }
.toggle{ display:flex; align-items:center; gap:8px; font-size:13px }
.toggle input{ width: 16px; height: 16px }
.footer{ display:flex; padding-top: 8px; }
.mode-btn{ display:flex; align-items:center; justify-content:center; gap:8px; background: rgba(255,255,255,.06); color:#fff; border:1px solid rgba(255,255,255,.12); border-radius:8px; padding:8px; cursor:pointer }
.mode-btn.round{ width: 40px; height: 40px; border-radius: 9999px; padding: 0 }
.mode-btn:hover{ filter: brightness(1.05) }
.mode-ico{ width:18px; text-align:center; pointer-events:none }
</style>
