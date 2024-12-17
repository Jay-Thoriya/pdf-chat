'use client'

import { useState, useRef, useEffect } from 'react'
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { FileUp, Send, FileText, Trash2 } from 'lucide-react'
import axios from 'axios'
import styles from './styles/Page.module.css'

interface UploadedFile {
  name: string;
}

export default function PDFChat() {
  const [messages, setMessages] = useState<{ role: 'user' | 'assistant'; content: string }[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([])
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files?.length) return

    const formData = new FormData()
    const newFiles: UploadedFile[] = []

    for (let i = 0; i < e.target.files.length; i++) {
      formData.append('files', e.target.files[i])
      newFiles.push({ name: e.target.files[i].name })
    }

    try {
      setIsLoading(true)
      await axios.post('http://127.0.0.1:5000/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setUploadedFiles(prev => [...prev, ...newFiles])
    } catch (error) {
      alert('Failed to upload PDFs. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleClearFiles = () => {
    setUploadedFiles([])

  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim()) return

    const userMessage = { role: 'user' as const, content: input }
    setMessages(prev => [...prev, userMessage])
    setInput('')

    try {
      setIsLoading(true)
      const response = await axios.post('http://127.0.0.1:5000/ask', {
        question: input
      })
      
      const assistantMessage = {
        role: 'assistant' as const,
        content: response.data.response
      }
      setMessages(prev => [...prev, assistantMessage])
    } catch (error) {
      alert('Failed to get response. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className={styles.container}>
      <h1 className={styles.title}>PDF Summarization Chatbot</h1>
      <div className={styles.layout}>
        <Card className={styles.uploadedFiles}>
          <h2 className={styles.title}>Uploaded PDFs</h2>
          <ScrollArea className={styles.messageList}>
            {uploadedFiles.map((file, index) => (
              <div key={index} className={styles.message}>
                <FileText className="h-5 w-5 text-blue-500" />
                <span className="text-sm">{file.name}</span>
              </div>
            ))}
          </ScrollArea>
        </Card>
        <Card className={styles.uploadButtons}>
          <div className="flex flex-col gap-2">
            <Button variant="outline" className="w-full justify-start gap-2">
              <FileUp className="h-4 w-4" />
              <label className="cursor-pointer">
                Upload PDFs
                <input
                  type="file"
                  multiple
                  accept=".pdf"
                  className="hidden"
                  onChange={handleFileUpload}
                  disabled={isLoading}
                />
              </label>
            </Button>
            <Button 
              variant="outline" 
              className="w-full justify-start gap-2"
              onClick={handleClearFiles}
              disabled={uploadedFiles.length === 0}
            >
              <Trash2 className="h-4 w-4" />
              Clear Files
            </Button>
          </div>
        </Card>
      </div>
      <Card className={styles.chatArea}>
        <ScrollArea className={styles.messageList}>
          {messages.map((message, index) => (
            <div key={index} className={`${styles.message} ${message.role === 'user' ? styles.userMessage : styles.assistantMessage}`}>
              <span className={`${styles.messageContent} ${message.role === 'user' ? styles.userMessageContent : styles.assistantMessageContent}`}>
                {message.content}
              </span>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </ScrollArea>
      </Card>
      <form onSubmit={handleSubmit} className={styles.inputForm}>
        <Input
          type="text"
          placeholder="Ask a question about your PDFs..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={isLoading}
        />
        <Button type="submit" disabled={isLoading}>
          <Send className="h-4 w-4" />
        </Button>
      </form>
    </div>
  )
}

