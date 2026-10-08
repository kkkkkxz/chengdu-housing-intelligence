<template>
  <div class="markdown-render" v-html="compiledContent" />
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  content: string
}>()

const compiledContent = computed(() => renderMarkdown(props.content || ''))

function renderMarkdown(raw: string): string {
  const lines = raw.split(/\r?\n/)
  let html = ''
  let inUnorderedList = false
  let inOrderedList = false
  let inBlockquote = false

  const closeLists = () => {
    if (inUnorderedList) {
      html += '</ul>'
      inUnorderedList = false
    }
    if (inOrderedList) {
      html += '</ol>'
      inOrderedList = false
    }
  }

  const closeBlockquote = () => {
    if (inBlockquote) {
      html += '</blockquote>'
      inBlockquote = false
    }
  }

  const closeStructures = () => {
    closeLists()
    closeBlockquote()
  }

  for (const line of lines) {
    const trimmed = line.trim()
    if (!trimmed) {
      closeStructures()
      html += '<p class="paragraph-separator"></p>'
      continue
    }

    const headingMatch = trimmed.match(/^(#\{1,6\})\s+(.*)$/)
    if (headingMatch) {
      closeStructures()
      const level = headingMatch[1].length
      html += `<h${level}>${transformInline(headingMatch[2].trim())}</h${level}>`
      continue
    }

    if (/^(-{3}|_{3}|\*{3})$/.test(trimmed)) {
      closeStructures()
      html += '<hr />'
      continue
    }

    const blockquoteMatch = trimmed.match(/^\>\s?(.*)$/)
    if (blockquoteMatch) {
      closeLists()
      if (!inBlockquote) {
        html += '<blockquote>'
        inBlockquote = true
      }
      html += `<p>${transformInline(blockquoteMatch[1])}</p>`
      continue
    } else {
      closeBlockquote()
    }

    const unorderedMatch = /^\s*[-+*]\s+/.test(line)
    const orderedMatch = /^\s*\d+\.\s+/.test(line)

    if (unorderedMatch) {
      closeBlockquote()
      if (!inUnorderedList) {
        closeLists()
        html += '<ul>'
        inUnorderedList = true
      }
      const text = transformInline(line.replace(/^\s*[-+*]\s+/, ''))
      html += `<li>${text}</li>`
      continue
    }

    if (orderedMatch) {
      if (!inOrderedList) {
        closeLists()
        html += '<ol>'
        inOrderedList = true
      }
      const text = transformInline(line.replace(/^\s*\d+\.\s+/, ''))
      html += `<li>${text}</li>`
      continue
    }

    closeLists()
    closeBlockquote()
    html += `<p>${transformInline(line)}</p>`
  }

  closeStructures()
  html = html.replace(/<p class="paragraph-separator"><\/p>/g, '<br />')
  return html || '<p>&nbsp;</p>'
}

function transformInline(text: string): string {
  const escaped = escapeHtml(text)

  return escaped
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/__(.+?)__/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/_(.+?)_/g, '<em>$1</em>')
    .replace(/`(.+?)`/g, '<code>$1</code>')
}

function escapeHtml(unsafe: string): string {
  return unsafe
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')
}
</script>