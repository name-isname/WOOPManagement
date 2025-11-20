<template>
  <div class="card" @contextmenu.prevent="$emit('context', { originalEvent: $event, item })" @mouseenter="hover = true"
    @mouseleave="hover = false">
    <div class="accent" />
    <div class="content">
      <div class="title">{{ item.name || item.title || '未命名' }}</div>
      <div class="meta"></div>
      <div class="desc">{{ item.description || item.outcome || '' }}</div>

      <!-- 详细信息：默认收起，悬停时展开，推动网格重新排布 -->
      <div class="details">
        <div class="row"><span class="label">愿望</span><span class="val">{{ item.wish || '-' }}</span></div>
        <div class="row"><span class="label">障碍</span><span class="val">{{ item.obstacle || '-' }}</span></div>
        <div class="row"><span class="label">计划</span><span class="val">{{ item.plan || '-' }}</span></div>
        <div class="row"><span class="label">结果</span><span class="val">{{ item.outcome || '-' }}</span></div>
        <div class="row"><span class="label">日期</span><span class="val">{{ item.datetime || '-' }}</span></div>
        <!-- ID removed from details -->
      </div>
    </div>

    <!-- quick actions -->
    <div class="actions" v-show="hover">
      <button class="icon" title="编辑" @click.stop="$emit('edit', item)">✏️</button>
      <button class="icon" title="删除" @click.stop="$emit('delete', item)">🗑️</button>
    </div>

    <!-- 已移除悬浮状态栏，避免遮挡按钮 -->
  </div>
</template>

<script setup>
import { ref } from 'vue'
const props = defineProps({ item: Object, index: { type: Number, default: 0 } })
const emit = defineEmits(['edit', 'delete', 'context'])
const hover = ref(false)

</script>

<style scoped>
.card {
  position: relative;
  display: flex;
  gap: 12px;
  background: var(--surface, #fff);
  border: 1px solid var(--surface-border, #cbd5e1);
  border-radius: 12px;
  padding: 14px 14px 14px 12px;
  min-height: 92px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, .03);
  transition: box-shadow .18s ease, border-color .18s ease, background-color .18s ease, max-height .18s ease, transform .18s ease;
}

.card:hover {
  box-shadow: 0 16px 40px rgba(0, 0, 0, .10);
  border-color: var(--surface-hover-border, #94a3b8);
  z-index: 5;
  transform: scale(1.03)
}

.accent {
  width: 4px;
  border-radius: 8px;
  background: var(--brand, #3b82f6)
}

.content {
  flex: 1;
  overflow: hidden
}

.title {
  font-weight: 700;
  font-size: 16px;
  color: var(--fg);
  white-space: normal;
  overflow: visible
}

.meta {
  margin-top: 4px;
  display: flex;
  gap: 8px;
  align-items: center;
  font-size: 12px;
  color: color-mix(in oklab, var(--fg) 65%, #94a3b8)
}

/* badge removed (index not displayed) */
.meta .id {
  display: none
}

.desc {
  margin-top: 6px;
  font-size: 13px;
  color: color-mix(in oklab, var(--fg) 65%, #94a3b8);
  white-space: normal;
  overflow: visible
}

/* always show details (no hover collapse) */
.details {
  display: block;
  margin-top: 10px
}

.row {
  display: flex;
  gap: 8px;
  align-items: flex-start;
  font-size: 12px;
  color: color-mix(in oklab, var(--fg) 70%, #94a3b8);
  line-height: 1.5
}

.row+.row {
  margin-top: 6px
}

.label {
  min-width: 42px;
  color: color-mix(in oklab, var(--fg) 55%, #94a3b8)
}

.val {
  flex: 1;
  word-break: break-word
}

.muted .label {
  color: #94a3b8
}

.actions {
  position: absolute;
  top: 8px;
  right: 8px;
  display: flex;
  gap: 6px;
  z-index: 20
}

.icon {
  background: color-mix(in oklab, var(--surface) 60%, #0000000f);
  border: 1px solid var(--surface-border);
  border-radius: 8px;
  padding: 4px 6px;
  cursor: pointer;
  min-width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center
}

.icon:hover {
  background: color-mix(in oklab, var(--surface) 40%, #0000001a)
}

.wish {
  margin-top: 6px;
  color: #64748b
}
</style>
