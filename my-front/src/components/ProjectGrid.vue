<template>
  <section>
    <div class="mb-4 flex justify-between items-center">
      <div class="text-sm text-gray-600">共 {{ total }} 项</div>
      <div class="flex gap-2">
        <button class="bg-green-600 text-white px-3 py-1 rounded disabled:opacity-50 disabled:cursor-not-allowed" @click="showModal = true" :disabled="!backendOnline">创建新项目</button>
        <button class="bg-blue-600 text-white px-3 py-1 rounded" @click="fetchList">刷新</button>
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
  <ProjectCard v-for="item in items" :key="item.id" :item="item"
         @link-ai="onLinkAI" @edit="onEdit" @delete="onDelete" @context="onCardContext" />
      </template>
    </div>

    <!-- 创建弹窗 -->
    <div v-if="showModal" class="fixed inset-0 flex items-center justify-center bg-black/40 z-50">
      <div class="modal-card rounded shadow p-4 w-96">
        <h3 class="font-semibold mb-2">创建新项目</h3>
        <div class="space-y-2 text-sm">
          <input v-model="form.name" placeholder="名称 (name)" class="w-full border px-2 py-1 modal-input" />
          <input v-model="form.wish" placeholder="愿望 (wish)" class="w-full border px-2 py-1 modal-input" />
          <input v-model="form.obstacle" placeholder="障碍 (obstacle)" class="w-full border px-2 py-1 modal-input" />
          <input v-model="form.plan" placeholder="计划 (plan)" class="w-full border px-2 py-1 modal-input" />
          <input v-model="form.outcome" placeholder="结果 (outcome)" class="w-full border px-2 py-1 modal-input" />
          <textarea v-model="form.description" placeholder="描述 (description)" class="w-full border px-2 py-1 modal-input" rows="3"></textarea>
        </div>

        <div class="mt-3 flex justify-end gap-2">
          <button class="px-3 py-1 rounded border" @click="showModal=false">取消</button>
          <button class="px-3 py-1 rounded bg-green-600 text-white" @click="createProject" :disabled="creating">{{ creating ? '创建中...' : '创建' }}</button>
        </div>
        <div v-if="formError" class="text-red-600 text-sm mt-2">{{ formError }}</div>
      </div>
    </div>

    <!-- 编辑弹窗 -->
    <div v-if="editModal" class="fixed inset-0 flex items-center justify-center bg-black/40 z-50">
      <div class="modal-card rounded shadow p-4 w-96">
        <h3 class="font-semibold mb-2">编辑项目</h3>
        <div class="space-y-2 text-sm">
          <input v-model="editForm.name" placeholder="名称 (name)" class="w-full border px-2 py-1 modal-input" />
          <input v-model="editForm.wish" placeholder="愿望 (wish)" class="w-full border px-2 py-1 modal-input" />
          <input v-model="editForm.obstacle" placeholder="障碍 (obstacle)" class="w-full border px-2 py-1 modal-input" />
          <input v-model="editForm.plan" placeholder="计划 (plan)" class="w-full border px-2 py-1 modal-input" />
          <input v-model="editForm.outcome" placeholder="结果 (outcome)" class="w-full border px-2 py-1 modal-input" />
          <textarea v-model="editForm.description" placeholder="描述 (description)" class="w-full border px-2 py-1 modal-input" rows="3"></textarea>
        </div>

        <div class="mt-3 flex justify-end gap-2">
          <button class="px-3 py-1 rounded border" @click="editModal=false">取消</button>
          <button class="px-3 py-1 rounded bg-blue-600 text-white" @click="updateProject" :disabled="editing">{{ editing ? '保存中...' : '保存' }}</button>
        </div>
        <div v-if="editError" class="text-red-600 text-sm mt-2">{{ editError }}</div>
      </div>
    </div>

    <!-- 删除确认弹窗 -->
    <div v-if="confirmDeleteModal" class="fixed inset-0 flex items-center justify-center bg-black/40 z-50">
      <div class="modal-card rounded shadow p-4 w-96">
        <h3 class="font-semibold mb-2">确认删除</h3>
        <p class="text-sm text-gray-600">确定要删除“{{ toDeleteItem?.name || '该项目' }}”吗？此操作不可撤回。</p>
        <div v-if="deleteError" class="text-red-600 text-sm mt-2">{{ deleteError }}</div>
        <div class="mt-3 flex justify-end gap-2">
          <button class="px-3 py-1 rounded border" @click="confirmDeleteModal=false" :disabled="deleteLoading">取消</button>
          <button class="px-3 py-1 rounded bg-red-600 text-white" @click="doDelete" :disabled="deleteLoading">{{ deleteLoading ? '删除中...' : '删除' }}</button>
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

const emit = defineEmits(['link-ai'])

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
    .then(r=>r.json())
    .then(d=>{ items.value = d.items || []; total.value = d.total || items.value.length })
    .catch(e=>{ console.error(e) })
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
</script>

<style scoped>
.context-menu{ min-width:140px }
/* 主题化：模态卡片与输入在暗色/亮色下适配 */
.modal-card{ background: var(--surface); border: 1px solid var(--surface-border) }
.modal-input{ background: transparent; color: var(--fg); border-color: var(--surface-border) }
.context-menu{ background: var(--surface); border: 1px solid var(--surface-border) }
/* 使用响应式 Grid，由最高卡片决定该行高度，其下各行整体下移 */
/* 骨架屏 */
.skeleton{ height: 92px; border-radius: 12px; border:1px solid var(--color-gray-200); background: linear-gradient(90deg, #f1f5f9 25%, #e2e8f0 37%, #f1f5f9 63%); background-size: 400% 100%; animation: shimmer 1.4s ease infinite }
@keyframes shimmer{ 0%{ background-position: 100% 0 } 100%{ background-position: -100% 0 } }
/* 空状态 */
.empty{ background:#fff; border:1px dashed var(--color-gray-400); border-radius:12px; padding:28px; text-align:center }
.empty-title{ font-weight:700; font-size:18px; color:#0f172a }
.empty-desc{ color:#475569; font-size:13px; margin-top:6px; margin-bottom:12px }
.btn{ background: var(--brand, #3b82f6); color:#fff; border:none; border-radius:8px; padding:8px 12px; cursor:pointer }
.btn:hover{ filter: brightness(1.05) }
</style>
