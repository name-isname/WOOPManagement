<template>
  <div class="card" @contextmenu.prevent="$emit('context', { originalEvent: $event, item })" @mouseenter="hover=true" @mouseleave="hover=false">
    <div class="accent" />
    <div class="content">
      <div class="header">
        <div class="title">{{ item.name || item.title || '未命名' }}</div>
        <div class="date">{{ item.datetime || '' }}</div>
      </div>
      
      <div class="desc" v-if="item.description">{{ item.description }}</div>

      <div class="details">
        <div class="woop-grid">
          <div class="woop-item">
            <span class="badge w">W</span>
            <span class="val">{{ item.wish || '-' }}</span>
          </div>
          <div class="woop-item">
            <span class="badge o">O</span>
            <span class="val">{{ item.obstacle || '-' }}</span>
          </div>
          <div class="woop-item">
            <span class="badge o2">O</span>
            <span class="val">{{ item.outcome || '-' }}</span>
          </div>
          <div class="woop-item">
            <span class="badge p">P</span>
            <span class="val">{{ item.plan || '-' }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- quick actions -->
    <div class="actions" :class="{ show: hover }">
      <button class="icon-btn" title="编辑" @click.stop="$emit('edit', item)">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>
      </button>
      <button class="icon-btn" title="链接 AI" @click.stop="$emit('link-ai', item)">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path></svg>
      </button>
      <button class="icon-btn danger" title="删除" @click.stop="$emit('delete', item)">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
const props = defineProps({ item: Object, index: { type: Number, default: 0 } })
const emit = defineEmits(['link-ai','edit','delete','context'])
const hover = ref(false)

</script>

<style scoped>
.card{
  position: relative;
  display: flex;
  flex-direction: column;
  background: var(--surface, #fff);
  border: 1px solid var(--surface-border, #e2e8f0);
  border-radius: 16px;
  padding: 24px;
  min-height: 220px;
  box-shadow: 0 1px 3px rgba(0,0,0,.04);
  transition: all .2s ease;
  overflow: hidden;
}
.card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(0,0,0,.08);
  border-color: color-mix(in oklab, var(--brand) 30%, var(--surface-border));
}

.accent {
  position: absolute; left: 0; top: 0; bottom: 0; width: 4px;
  background: var(--brand, #3b82f6); opacity: 0; transition: opacity .2s;
}
.card:hover .accent { opacity: 1; }

.content { flex: 1; display: flex; flex-direction: column; gap: 8px; }

.header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 4px; }
.title { font-weight: 600; font-size: 16px; color: var(--fg); line-height: 1.4; }
.date { font-size: 12px; color: #94a3b8; white-space: nowrap; margin-left: 8px; }

.desc { font-size: 12px; color: #94a3b8; line-height: 1.5; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; margin-bottom: 16px; }

.woop-grid { display: grid; gap: 12px; margin-top: auto; }
.woop-item { display: flex; align-items: flex-start; gap: 12px; font-size: 15px; color: #334155; font-weight: 500; }
.val { white-space: normal; overflow: visible; word-break: break-word; line-height: 1.5; flex: 1; }

.badge {
  display: inline-flex; align-items: center; justify-content: center;
  width: 24px; height: 24px; border-radius: 6px;
  font-size: 12px; font-weight: 700; color: #fff; flex-shrink: 0;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  margin-top: 2px; /* Align with text */
}
.badge.w { background: #3b82f6; } /* Wish */
.badge.o { background: #f59e0b; } /* Obstacle */
.badge.o2 { background: #10b981; } /* Outcome */
.badge.p { background: #8b5cf6; } /* Plan */

.actions {
  position: absolute; top: 12px; right: 12px;
  display: flex; gap: 6px;
  opacity: 0; transform: translateX(10px); transition: all .2s ease;
  background: rgba(255,255,255,0.9); backdrop-filter: blur(4px);
  padding: 4px; border-radius: 8px; border: 1px solid #e2e8f0;
}
.actions.show { opacity: 1; transform: translateX(0); }

.icon-btn {
  width: 28px; height: 28px; display: flex; align-items: center; justify-content: center;
  border: none; background: transparent; color: #64748b; border-radius: 6px; cursor: pointer;
  transition: all .15s;
}
.icon-btn:hover { background: #f1f5f9; color: #3b82f6; }
.icon-btn.danger:hover { background: #fef2f2; color: #ef4444; }

</style>
