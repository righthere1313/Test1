<template>
  <div class="chat-sidebar">
    <div class="profile-section">
      <div class="avatar" @click="editAvatar">
        <img v-if="store.user.avatar" :src="store.user.avatar" alt="头像" class="avatar-img">
      </div>
      <div class="username-wrapper">
        <span
          v-if="!isEditingUsername"
          class="username"
          @click="isEditingUsername = true"
        >
          {{ store.user.username }}
        </span>
        <input
          v-else
          v-model="editUsername"
          @blur="saveUsername"
          @keyup.enter="saveUsername"
          class="username-input"
          ref="usernameInput"
        />
      </div>
    </div>
    <div class="info-section">
      <h4>个人信息</h4>
      <div class="info-display">
        <div class="info-item">
          <span class="info-label">教师姓名：</span>
          <span class="info-value">{{
            store.user.teacherName || "未设置"
          }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">教学学科：</span>
          <span class="info-value">{{ store.user.subject || "未设置" }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">学校名称：</span>
          <span class="info-value">{{
            store.user.schoolName || "未设置"
          }}</span>
        </div>
        <p class="info-note">这些信息将作为课件署名</p>
      </div>
    </div>
    <div class="history-card">
      <div class="history-section">
        <div class="todo-header">
          <div>待办事项</div>
          <div class="todo-actions" ref="todoActionsRef">
            <div class="todo-input-wrapper">
              <button @click="toggleAddTodo" class="todo-btn add">
                <span class="btn-icon">+</span>
              </button>
              <div v-if="showAddTodo" class="todo-edit-bubble">
                <input 
                  v-model="newTodoContent" 
                  @keyup.enter="saveTodo"
                  @keyup.esc="cancelAddTodo"
                  ref="todoInputRef"
                  class="todo-input"
                  placeholder="输入待办事项..."
                  autofocus
                />
                <div class="todo-input-buttons">
                  <button @click="cancelAddTodo" class="todo-input-btn cancel">取消</button>
                  <button @click="saveTodo" class="todo-input-btn confirm">确认</button>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="history-list">
          <div
            v-for="(item, index) in todos"
            :key="index"
            class="history-item todo-item"
            :class="{ done: item.done }"
          >
            <span class="todo-content">{{ item.content }}</span>
            <div class="todo-right">
              <button @click="deleteTodo(index)" class="todo-btn delete">
                <span class="btn-icon">-</span>
              </button>
              <button @click="toggleTodo(index)" class="todo-checkbox" :class="{ checked: item.done }">
                <span v-if="item.done" class="checkmark">✓</span>
              </button>
            </div>
          </div>
          <div v-if="todos.length === 0" class="empty-todo">
            暂无待办事项
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch, onUnmounted } from "vue";
import { useRouter } from "vue-router";
import store from "../store";

const router = useRouter();
const isEditingUsername = ref(false);
const editUsername = ref("");
const usernameInput = ref(null);
const todoInputRef = ref(null);
const todoActionsRef = ref(null);

const STORAGE_KEY = "chat-todos";

const loadTodos = () => {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      return JSON.parse(saved);
    }
  } catch (e) {
    console.error("加载待办事项失败:", e);
  }
  return [
    { content: "准备数学课件", done: false },
    { content: "批改作业", done: true },
    { content: "准备家长会", done: false },
  ];
};

const todos = ref(loadTodos());

const saveTodosToStorage = () => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(todos.value));
  } catch (e) {
    console.error("保存待办事项失败:", e);
  }
};

const showAddTodo = ref(false);
const newTodoContent = ref("");

const toggleAddTodo = () => {
  showAddTodo.value = !showAddTodo.value;
  if (showAddTodo.value) {
    newTodoContent.value = "";
    nextTick(() => {
      todoInputRef.value?.focus();
    });
  }
};

const saveTodo = () => {
  if (newTodoContent.value && newTodoContent.value.trim()) {
    todos.value.push({ content: newTodoContent.value.trim(), done: false });
    saveTodosToStorage();
  }
  showAddTodo.value = false;
  newTodoContent.value = "";
};

const cancelAddTodo = () => {
  showAddTodo.value = false;
  newTodoContent.value = "";
};

const handleClickOutside = (event) => {
  if (showAddTodo.value && todoActionsRef.value && !todoActionsRef.value.contains(event.target)) {
    cancelAddTodo();
  }
};

onMounted(() => {
  document.addEventListener("click", handleClickOutside);
});

onUnmounted(() => {
  document.removeEventListener("click", handleClickOutside);
});

const deleteTodo = (index) => {
  todos.value.splice(index, 1);
  saveTodosToStorage();
};

const toggleTodo = (index) => {
  todos.value[index].done = !todos.value[index].done;
  saveTodosToStorage();
};

const editAvatar = () => {
  router.push("/profile");
};

const saveUsername = () => {
  if (editUsername.value.trim()) {
    store.updateUser({ username: editUsername.value.trim() });
  }
  isEditingUsername.value = false;
};

const goToProfile = () => {
  router.push("/profile");
};
</script>

<style scoped>
.chat-sidebar {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: white;
  border-radius: 4px;
  overflow: hidden;
  padding: 16px;
  gap: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
  min-height: 0;
}

.profile-section {
  padding: 16px 16px;
  text-align: center;
  border-bottom: 1px solid #e9ecef;
  background: white;
  flex-shrink: 0;
}

.avatar {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  border: 2px solid #8ab4aa;
  background: #bdd6cd;
  color: #0f5132;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 10px;
  cursor: pointer;
  transition: transform 0.2s ease;
}

.avatar:hover {
  transform: scale(1.05);
}

.avatar-icon {
  font-size: 26px;
}

.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 50%;
}

.username-wrapper {
  display: flex;
  justify-content: center;
}

.username {
  font-size: 14px;
  font-weight: 600;
  color: #212529;
  cursor: pointer;
  padding: 3px 6px;
  border-radius: 6px;
  transition: background 0.2s ease;
}

.username:hover {
  background: #f8f9fa;
}

.username-input {
  font-size: 16px;
  font-weight: 600;
  color: #212529;
  text-align: center;
  padding: 4px 8px;
  border: 2px solid #1a1a1a;
  border-radius: 6px;
  outline: none;
  width: 100%;
  max-width: 200px;
}

.info-section {
  padding: 14px 16px;
  background: white;
  border-radius: 6px;
  flex-shrink: 0;
}

.history-card {
  flex: 1;
  background: #c1dad2;
  border-radius: 6px;
  overflow: hidden;
  position: relative;
  min-height: 0;
}

.info-section h4,
.history-section h4 {
  font-size: 13px;
  color: #212529;
  margin-bottom: 12px;
  font-weight: 600;
}

.history-section h4 {
  color: rgb(0, 0, 0);
  margin: 0;
}

.info-display {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
}

.info-label {
  color: #6c757d;
}

.info-value {
  color: #212529;
  font-weight: 500;
}

.info-note {
  font-size: 11px;
  color: #6c757d;
  margin-top: 8px;
  font-style: italic;
  text-align: center;
}

.history-section {
  padding: 20px;
  height: 100%;
  display: flex;
  flex-direction: column;
  position: relative;
  z-index: 1;
  min-height: 0;
  overflow: hidden;
}

.todo-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  font-weight: 700;
}

.todo-actions {
  display: flex;
  gap: 4px;
  position: relative;
}

.todo-input-wrapper {
  position: relative;
}

.todo-edit-bubble {
  position: absolute;
  right: 0;
  top: 30px;
  width: 200px;
  background: #ffffff;
  border: 2px solid #8ab4aa;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  padding: 12px;
  z-index: 1000;
}

.todo-edit-bubble::after {
  content: '';
  position: absolute;
  top: -8px;
  right: 6px;
  border-width: 0 8px 8px 8px;
  border-style: solid;
  border-color: transparent transparent white transparent;
}

.todo-input {
  width: 100%;
  padding: 8px 10px;
  border: 2px solid #ffffff;
  background: #bdd6cd;
  border-radius: 6px;
  font-size: 13px;
  outline: none;
  margin-bottom: 8px;
  box-sizing: border-box;
}

.todo-input-buttons {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.todo-input-btn {
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  border: none;
  transition: all 0.2s ease;
}

.todo-input-btn.cancel {
  background: #e9ecef;
  color: #6c757d;
}

.todo-input-btn.cancel:hover {
  background: #dee2e6;
}

.todo-input-btn.confirm {
  background: #8ab4aa;
  color: white;
}

.todo-input-btn.confirm:hover {
  background: #64a596;
}

.todo-btn {
  width: 22px;
  height: 22px;
  border: 2px solid #312f2f;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  background: white;
  color: #312f2f;
  padding: 0;
}

.btn-icon {
  font-size: 18px;
  font-weight: 600;
  line-height: 1;
  margin-top: -1px;
}

.todo-btn.add {
  border-color: #999999;
  color: #999999;
}

.todo-btn.add:hover {
  background: #999999;
  color: white;
}

.todo-btn.delete{
    background: #ffdfdf;
    border-color: #fda3ad;
    color: #fda3ad;
}

.todo-btn.delete:hover {
  background: #e28b94;
  color: white;
}

.history-list {
  flex: 1;
  overflow-y: auto;
}

.history-item {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 8px 10px;
  background-color: #fff;
  border:2px solid #8ab4aa;
  border-radius: 8px;
  margin: 0 auto;
  margin-bottom: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.todo-content {
  flex: 1;
  font-size: 13px;
  color: #000000;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.todo-item.done .todo-content {
  text-decoration: line-through;
  opacity: 0.6;
}

.todo-right {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.todo-checkbox {
  width: 22px;
  height: 22px;
  border: 2px solid #64a596;
  border-radius: 4px;
  background: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  transition: all 0.2s ease;
  color: #64a596;
}
.todo-checkbox:hover {
  background: #64a596;
  border-color: #64a596;
}

.todo-checkbox.checked {
  background: #64a596;
  border-color: #64a596;
}

.checkmark {
  color: white;
  font-size: 12px;
  font-weight: bold;
  line-height: 1;
  margin-top: -1px;
}

.empty-todo {
  text-align: center;
  color: #6c757d;
  font-size: 13px;
  padding: 20px;
}
</style>
