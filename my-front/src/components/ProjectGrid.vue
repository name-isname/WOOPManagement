<template>
  <section>
    <div class="mb-6 flex justify-between items-center">
      <div class="text-sm font-medium text-slate-500">共 {{ total }} 个项目</div>
      <div class="flex gap-3">
        <button class="btn-action primary" @click="showModal = true" :disabled="!backendOnline">
          <span class="icon">+</span> 创建项目
        </button>
        <button class="btn-action magic" @click="$emit('link-ai', null)">
          <span class="icon">✨</span> AI 助手
        </button>
        <button class="btn-action outline" @click="fetchList" title="刷新列表">
          <span class="icon">↻</span>
        </button>
      </div>
    </div>

    <div v-if="!backendOnline" class="mb-4 p-3 rounded border text-sm bg-yellow-50 border-yellow-200 text-yellow-700">
      后端未连接（127.0.0.1:8000）。请先启动后端，再点击“刷新”。
    </div>

    <!-- 列表区域：加载骨架 / 空状态 / 卡片网格 -->
  <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
      <!-- 骨架屏 -->
      <template v-if="loading">
        <div v-for="n in 6" :key="'sk-'+n" class="skeleton" />
      </template>
      <!-- 空状态 -->
      <template v-else-if="!items.length">
        <div class="empty col-span-full">
          <div class="empty-title">还没有项目</div>
          <div class="empty-desc">点击右上角“创建新项目”开始你的第一个 WOOP。</div>
          <button class="btn" @click="showModal=true">创建新项目</button>
        </div>
      </template>
      <!-- 卡片 -->
      <template v-else>
        <div v-for="(item, i) in items" :key="item.id" class="dnd-item" draggable="true"
             @dragstart="onDragStart(i)" @dragover.prevent @drop="onDrop(i)">
          <ProjectCard :item="item" :index="i+1" @link-ai="onLinkAI" @edit="onEdit" @delete="onDelete" @context="onCardContext" />
        </div>
      </template>
    </div>

    <!-- 创建弹窗：与编辑弹窗同步风格 -->
    <div v-if="showModal" class="fixed inset-0 z-50">
      <div class="backdrop" @click="closeCreate"></div>
      <div class="edit-panel" role="dialog" aria-modal="true">
        <div class="edit-header">
          <div>
            <div class="edit-title">创建新项目</div>
            <div class="edit-sub">填写 WOOP 的关键信息</div>
          </div>
          <button class="icon-btn" title="关闭" @click="closeCreate">×</button>
        </div>

        <div class="edit-body">
          <label class="field">
            <span class="label">名称</span>
            <input v-model="form.name" class="input" placeholder="示例：学习" />
          </label>
          <label class="field">
            <span class="label">愿望</span>
            <input v-model="form.wish" class="input" placeholder="我想要…" />
          </label>
          <label class="field">
            <span class="label">障碍</span>
            <input v-model="form.obstacle" class="input" placeholder="我会遇到…" />
          </label>
          <label class="field">
            <span class="label">计划</span>
            <input v-model="form.plan" class="input" placeholder="如果…那么我就…" />
          </label>
          <label class="field">
            <span class="label">结果</span>
            <input v-model="form.outcome" class="input" placeholder="我将达成…" />
          </label>
          <label class="field field-col">
            <span class="label">描述</span>
            <textarea v-model="form.description" class="input" rows="4" placeholder="补充说明（可选）"></textarea>
          </label>
        </div>

        <div class="edit-footer">
          <div class="grow"></div>
          <button class="btn ghost" @click="closeCreate" :disabled="creating">取消</button>
          <button class="btn primary" @click="createProject" :disabled="creating">{{ creating ? '创建中…' : '创建' }}</button>
        </div>
        <div v-if="formError" class="msg-err">{{ formError }}</div>
      </div>
    </div>

    <!-- 编辑弹窗：参考后图的现代卡片风格 -->
    <div v-if="editModal" class="fixed inset-0 z-50">
      <div class="backdrop" @click="closeEdit"></div>
      <div class="edit-panel" role="dialog" aria-modal="true">
        <div class="edit-header">
          <div>
            <div class="edit-title">编辑项目</div>
            <div class="edit-sub">请完善 WOOP 的关键信息</div>
          </div>
          <button class="icon-btn" title="关闭" @click="closeEdit">×</button>
        </div>

        <div class="edit-body">
          <label class="field">
            <span class="label">名称</span>
            <input v-model="editForm.name" class="input" placeholder="示例：学习" />
          </label>
          <label class="field">
            <span class="label">愿望</span>
            <input v-model="editForm.wish" class="input" placeholder="我想要…" />
          </label>
          <label class="field">
            <span class="label">障碍</span>
            <input v-model="editForm.obstacle" class="input" placeholder="我会遇到…" />
          </label>
          <label class="field">
            <span class="label">计划</span>
            <input v-model="editForm.plan" class="input" placeholder="如果…那么我就…" />
          </label>
          <label class="field">
            <span class="label">结果</span>
            <input v-model="editForm.outcome" class="input" placeholder="我将达成…" />
          </label>
          <label class="field field-col">
            <span class="label">描述</span>
            <textarea v-model="editForm.description" class="input" rows="4" placeholder="补充说明（可选）"></textarea>
          </label>
        </div>

        <div class="edit-footer">
          <div class="grow"></div>
          <button class="btn ghost" @click="closeEdit">取消</button>
          <button class="btn primary" @click="updateProject" :disabled="editing">{{ editing ? '保存中…' : '保存' }}</button>
        </div>
        <div v-if="editError" class="msg-err">{{ editError }}</div>
      </div>
    </div>

    <!-- 删除确认弹窗 -->
    <div v-if="confirmDeleteModal" class="fixed inset-0 flex items-center justify-center z-50">
      <div class="backdrop" @click="confirmDeleteModal=false"></div>
      <div class="modal-card-card w-96" role="dialog" aria-modal="true" aria-labelledby="del-title">
        <div class="modal-head">
          <div class="icon-wrap" aria-hidden="true">🗑️</div>
          <div>
            <h3 id="del-title" class="modal-title">确认删除</h3>
            <div class="modal-sub">此操作将永久删除该项目，无法恢复。</div>
          </div>
        </div>
        <div class="modal-body">
          <p class="text">你确定要删除 <strong>“{{ toDeleteItem?.name || '该项目' }}”</strong> 吗？</p>
          <div v-if="deleteError" class="text-red-600 text-sm mt-2">{{ deleteError }}</div>
        </div>
        <div class="modal-actions">
          <button class="btn ghost" @click="confirmDeleteModal=false" :disabled="deleteLoading">取消</button>
          <button class="btn danger" @click="doDelete" :disabled="deleteLoading">{{ deleteLoading ? '删除中...' : '确认删除' }}</button>
        </div>
      </div>
    </div>

    <!-- 右键菜单 -->
    <div v-if="menu.visible" :style="menuStyle" class="context-menu shadow p-2 rounded">
      <button class="block px-3 py-1 hover:bg-slate-100 w-full text-left" @click="menuEdit">编辑</button>
      <button class="block px-3 py-1 hover:bg-slate-100 w-full text-left" @click="menuDelete">删除</button>
      <button class="block px-3 py-1 hover:bg-slate-100 w-full text-left" @click="menuLinkAI">链接 AI</button>
    </div>
  </section>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
const props = defineProps({ backendOnline: { type: Boolean, default: true } })
import ProjectCard from './ProjectCard.vue'

const emit = defineEmits(['link-ai','backend-online'])

// 优先使用环境变量，默认使用 127.0.0.1 以规避某些代理对 localhost 的拦截
const apiBase = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000'
const items = ref([])
const total = ref(0)
const loading = ref(false)

const menu = ref({ visible:false, x:0, y:0, item:null })

// delete confirm state
const confirmDeleteModal = ref(false)
const toDeleteItem = ref(null)
const deleteLoading = ref(false)
const deleteError = ref('')

// create modal state
const showModal = ref(false)
const creating = ref(false)
const formError = ref('')
const form = ref({ name:'示例', wish:'', obstacle:'', plan:'', outcome:'', description:'' })

// edit modal state
const editModal = ref(false)
const editing = ref(false)
const editError = ref('')
const editForm = ref({ id:null, name:'', wish:'', obstacle:'', plan:'', outcome:'', description:'' })

function fetchList(){
  loading.value = true
  fetch(`${apiBase}/woops/?page=1&size=50`)
    .then(r=>{
      if(!r.ok) throw new Error('Status ' + r.status)
      return r.json()
    })
    .then(d=>{ items.value = d.items || []; total.value = d.total || items.value.length; emit('backend-online', true) })
    .catch(e=>{ console.error(e); emit('backend-online', false) })
    .finally(()=>{ loading.value = false })
}

function onLinkAI(item){
  emit('link-ai', item)
}

function onEdit(item){
  // 打开编辑弹窗并填充表单
  editForm.value = { id: item.id, name:item.name||'', wish:item.wish||'', obstacle:item.obstacle||'', plan:item.plan||'', outcome:item.outcome||'', description:item.description||'' }
  editError.value = ''
  editModal.value = true
}

function onDelete(item){
  // 使用自定义弹窗确认，兼容某些浏览器或内嵌环境禁用 window.confirm 的情况
  toDeleteItem.value = item
  deleteError.value = ''
  confirmDeleteModal.value = true
}

async function doDelete(){
  if (!toDeleteItem.value) return
  deleteLoading.value = true
  deleteError.value = ''
  try{
    const res = await fetch(`${apiBase}/woops/${toDeleteItem.value.id}`, { method: 'DELETE' })
    if (!res.ok){
      const txt = await res.text()
      deleteError.value = `删除失败: ${txt || ('Status ' + res.status)}`
      return
    }
    confirmDeleteModal.value = false
    toDeleteItem.value = null
    fetchList()
  }catch(err){
    deleteError.value = `网络错误，删除未完成: ${err?.message || err}`
  }finally{
    deleteLoading.value = false
  }
}

function showMenu(e, item){
  e.preventDefault()
  menu.value = { visible:true, x:e.clientX, y:e.clientY, item }
}

function hideMenu(){ menu.value.visible=false }

function menuEdit(){ onEdit(menu.value.item); hideMenu() }
function menuDelete(){ onDelete(menu.value.item); hideMenu() }
function menuLinkAI(){ emit('link-ai', menu.value.item); hideMenu() }

function onCardContext(payload){
  const { originalEvent, item } = payload || {}
  if (originalEvent) showMenu(originalEvent, item)
}

onMounted(()=>{ fetchList(); window.addEventListener('click', hideMenu) })

const menuStyle = computed(()=>({ position:'fixed', left: menu.value.x + 'px', top: menu.value.y + 'px', zIndex:1000 }))

async function createProject(){
  formError.value = ''
  creating.value = true
  try{
    // 基础必填校验，避免 422
    const required = ['name','wish','obstacle','plan','outcome']
    for (const k of required){
      if (!String(form.value[k] ?? '').trim()){
        throw new Error('请填写所有必填字段（名称/愿望/障碍/计划/结果）')
      }
    }
    const res = await fetch(`${apiBase}/woops/`, { method:'POST', headers:{ 'Content-Type':'application/json' }, body: JSON.stringify(form.value) })
    if (!res.ok){
      const txt = await res.text()
      throw new Error(txt || ('Status ' + res.status))
    }
    // success
    showModal.value = false
    form.value = { name:'示例', wish:'', obstacle:'', plan:'', outcome:'', description:'' }
    fetchList()
  }catch(e){
    formError.value = e.message || String(e)
  }finally{ creating.value = false }
}

async function updateProject(){
  editError.value = ''
  editing.value = true
  try{
    const required = ['name','wish','obstacle','plan','outcome']
    for (const k of required){
      if (!String(editForm.value[k] ?? '').trim()){
        throw new Error('请填写所有必填字段（名称/愿望/障碍/计划/结果）')
      }
    }

    const id = editForm.value.id
    // 构造仅包含非空值的更新数据，避免触发最小长度校验
    const payload = {}
    for (const k of ['name','wish','obstacle','plan','outcome','description']){
      const v = editForm.value[k]
      if (v !== undefined && v !== null && String(v).trim() !== ''){
        payload[k] = v
      }
    }

    const res = await fetch(`${apiBase}/woops/${id}`, { method:'PUT', headers:{ 'Content-Type':'application/json' }, body: JSON.stringify(payload) })
    if (!res.ok){
      const txt = await res.text()
      throw new Error(txt || ('Status ' + res.status))
    }
    editModal.value = false
    fetchList()
  }catch(e){
    editError.value = e.message || String(e)
  }finally{
    editing.value = false
  }
}

function closeCreate(){ showModal.value = false }
function closeEdit(){ editModal.value = false }

// ===== 拖拽排序 =====
const dragIndex = ref(-1)
function onDragStart(i){ dragIndex.value = i }
function onDrop(i){
  if (dragIndex.value < 0 || dragIndex.value === i) return
  const arr = items.value.slice()
  const [moved] = arr.splice(dragIndex.value, 1)
  arr.splice(i, 0, moved)
  items.value = arr
  dragIndex.value = -1
  persistRanks()
}

async function persistRanks(){
  // 仅对排序发生变化的项提交 rank，rank 从 1 开始
  const updates = []
  for (let i=0;i<items.value.length;i++){
    const it = items.value[i]
    const desired = i + 1
    if (it.rank !== desired){
      updates.push(fetch(`${apiBase}/woops/${it.id}`, { method:'PUT', headers:{ 'Content-Type':'application/json' }, body: JSON.stringify({ rank: desired }) }))
      it.rank = desired
    }
  }
  if (updates.length){
    try{ await Promise.allSettled(updates) }catch{}
  }
}

defineExpose({ fetchList })
</script>

<style scoped>
.context-menu{ min-width:140px }
/* 主题化：模态卡片与输入在暗色/亮色下适配 */
.modal-card{ background: var(--surface); border: 1px solid var(--surface-border) }
.modal-card-card{ background: var(--surface); border: 1px solid var(--surface-border); border-radius: 12px; box-shadow: 0 18px 50px rgba(11,18,32,0.28); padding: 16px; position: relative; overflow: hidden; transform: translateY(0); animation: pop .12s ease }
.backdrop{ position: fixed; inset:0; background: rgba(0,0,0,.45); backdrop-filter: blur(2px) }
@keyframes pop{ from{ transform: translateY(-6px) scale(.995); opacity:0 } to{ transform: translateY(0) scale(1); opacity:1 } }
.modal-head{ display:flex; gap:12px; align-items:center; margin-bottom:8px }
.icon-wrap{ width:44px; height:44px; display:flex; align-items:center; justify-content:center; border-radius:9999px; background: color-mix(in oklab, var(--brand) 18%, #fee2e2); color: color-mix(in oklab, var(--brand) 60%, #ef4444); font-size:20px; border:1px solid color-mix(in oklab, var(--brand) 8%, #00000008) }
.modal-title{ font-size:16px; font-weight:700 }
.modal-sub{ font-size:12px; color: color-mix(in oklab, var(--fg) 60%, #94a3b8) }
.modal-body{ padding:6px 0 10px }
.modal-body .text{ color: var(--fg); font-size:14px }
.modal-actions{ display:flex; justify-content:flex-end; gap:10px; padding-top:8px; border-top: 1px dashed color-mix(in oklab, var(--surface-border) 60%, #00000008); margin-top:8px }
.btn.ghost{ background: transparent; color: var(--fg); border:1px solid var(--surface-border); border-radius:8px; padding: 8px 12px }
.btn.danger, .btn.danger:disabled{ background: linear-gradient(180deg,#ef4444,#dc2626); color:#fff; border:none; border-radius:8px; padding: 8px 12px }
.btn.danger:hover{ filter: brightness(.95) }
.btn:disabled{ opacity:.6; cursor:not-allowed }
.msg-err{ color:#ef4444; font-size: 12px; padding: 6px 16px }

/* 新增按钮样式 */
.btn-action {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 8px 16px; border-radius: 8px; font-size: 14px; font-weight: 500;
  cursor: pointer; transition: all .2s ease; border: 1px solid transparent;
}
.btn-action:active { transform: scale(0.98); }
.btn-action .icon { font-family: sans-serif; line-height: 1; font-size: 1.1em; }

.btn-action.primary {
  background: var(--brand, #3b82f6); color: #fff;
  box-shadow: 0 2px 4px rgba(59, 130, 246, 0.2);
}
.btn-action.primary:hover { filter: brightness(1.08); box-shadow: 0 4px 8px rgba(59, 130, 246, 0.3); }
.btn-action.primary:disabled { background: #94a3b8; box-shadow: none; cursor: not-allowed; }

.btn-action.magic {
  background: linear-gradient(135deg, #8b5cf6, #d946ef); color: #fff;
  box-shadow: 0 2px 4px rgba(139, 92, 246, 0.25);
}
.btn-action.magic:hover { filter: brightness(1.1); box-shadow: 0 4px 10px rgba(139, 92, 246, 0.35); }

.btn-action.outline {
  background: transparent; border-color: var(--surface-border); color: var(--fg);
  padding: 8px 12px;
}
.btn-action.outline:hover { background: var(--surface-border); }

/* 修复丢失的编辑弹窗样式 */
.edit-panel{ position: fixed; inset: 50% auto auto 50%; transform: translate(-50%, -50%); width: 560px; max-width: 92vw; background: var(--surface); color: var(--fg); border: 1px solid var(--surface-border); border-radius: 16px; box-shadow: 0 24px 60px rgba(0,0,0,.2); display:flex; flex-direction: column; max-height: 90vh; min-height: 40vh; overflow: hidden; z-index: 100; }
.edit-header{ display:flex; align-items: center; justify-content: space-between; padding: 14px 16px; border-bottom: 1px solid var(--surface-border) }
.edit-title{ font-size: 16px; font-weight: 700 }
.edit-sub{ font-size: 12px; color: color-mix(in oklab, var(--fg) 60%, #94a3b8) }
.icon-btn{ width:28px; height:28px; display:flex; align-items:center; justify-content:center; border:1px solid var(--surface-border); border-radius: 8px; background: transparent; cursor: pointer }
.icon-btn:hover{ background: color-mix(in oklab, var(--surface) 70%, #00000010) }
.edit-body{ padding: 14px 16px 12px; display: grid; grid-template-columns: 1fr; gap: 12px; flex: 1 1 auto; overflow: auto }
.field{ display:flex; flex-direction: column; gap: 6px }
.field-col{ grid-column: 1 / -1; margin-bottom: 12px }
.label{ font-size: 12px; color: color-mix(in oklab, var(--fg) 60%, #94a3b8) }
.input{ background: var(--surface); color: var(--fg); border: 1px solid var(--surface-border); border-radius: 8px; padding: 10px 12px; width: 100%; box-sizing: border-box }
.input[type="textarea"], textarea.input{ min-height: 120px }
.input:focus{ outline: none; border-color: color-mix(in oklab, var(--brand) 60%, var(--surface-border)); box-shadow: 0 0 0 3px color-mix(in oklab, var(--brand) 18%, transparent) }
.edit-footer{ display:flex; align-items:center; gap:8px; padding: 12px 16px; border-top: 1px solid var(--surface-border); background: var(--surface); margin-top: auto }
</style>
