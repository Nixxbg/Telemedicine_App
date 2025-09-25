"use client";

import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Message, PatientProfile, DoctorProfile } from "@/types";

interface MessageInterfaceProps {
  currentUserId: string;
  currentUserType: 'patient' | 'doctor';
  recipient: PatientProfile | DoctorProfile;
  messages: Message[];
  onSendMessage: (content: string, messageType?: 'text' | 'file') => Promise<void>;
  onMarkAsRead: (messageId: string) => Promise<void>;
  loading?: boolean;
}

export function MessageInterface({
  currentUserId,
  currentUserType,
  recipient,
  messages,
  onSendMessage,
  onMarkAsRead,
  loading = false
}: MessageInterfaceProps) {
  const [newMessage, setNewMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Mark unread messages as read
    const unreadMessages = messages.filter(msg => 
      !msg.is_read && msg.sender_id !== currentUserId
    );
    
    unreadMessages.forEach(msg => {
      onMarkAsRead(msg.id);
    });
  }, [messages, currentUserId, onMarkAsRead]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!newMessage.trim()) return;

    await onSendMessage(newMessage.trim());
    setNewMessage('');
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // In a real implementation, you would upload the file and get a URL
    // For now, we'll just send the file name as a message
    await onSendMessage(`[File: ${file.name}]`, 'file');
    
    // Clear the file input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const formatMessageTime = (dateString: string) => {
    const messageDate = new Date(dateString);
    const now = new Date();
    const diffInHours = (now.getTime() - messageDate.getTime()) / (1000 * 60 * 60);

    if (diffInHours < 24) {
      return messageDate.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit'
      });
    } else if (diffInHours < 24 * 7) {
      return messageDate.toLocaleDateString('en-US', {
        weekday: 'short',
        hour: '2-digit',
        minute: '2-digit'
      });
    } else {
      return messageDate.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    }
  };

  const getRecipientName = () => {
    return `${recipient.first_name} ${recipient.last_name}`;
  };

  const getRecipientRole = () => {
    if (currentUserType === 'patient') {
      return `Dr. ${recipient.last_name} - ${(recipient as DoctorProfile).specialization}`;
    } else {
      return `Patient: ${(recipient as PatientProfile).username}`;
    }
  };

  const groupMessagesByDate = (messages: Message[]) => {
    const groups: Record<string, Message[]> = {};
    
    messages.forEach(message => {
      const date = new Date(message.created_at).toDateString();
      if (!groups[date]) {
        groups[date] = [];
      }
      groups[date].push(message);
    });

    return groups;
  };

  const groupedMessages = groupMessagesByDate(messages);

  return (
    <Card className="w-full max-w-4xl mx-auto h-[600px] flex flex-col">
      <CardHeader className="shrink-0">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>{getRecipientName()}</CardTitle>
            <CardDescription>{getRecipientRole()}</CardDescription>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
            <span className="text-sm text-gray-600">Online</span>
          </div>
        </div>
      </CardHeader>

      <CardContent className="flex-1 flex flex-col min-h-0">
        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto mb-4 p-4 border rounded-lg bg-gray-50">
          {Object.keys(groupedMessages).length === 0 ? (
            <div className="text-center text-gray-500 py-8">
              <p>No messages yet.</p>
              <p className="text-sm mt-2">Start a conversation below.</p>
            </div>
          ) : (
            Object.entries(groupedMessages).map(([date, dayMessages]) => (
              <div key={date}>
                {/* Date separator */}
                <div className="text-center my-4">
                  <span className="bg-white px-3 py-1 rounded-full text-sm text-gray-600 border">
                    {new Date(date).toLocaleDateString('en-US', {
                      weekday: 'long',
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric'
                    })}
                  </span>
                </div>

                {/* Messages for this date */}
                {dayMessages.map((message) => {
                  const isOwn = message.sender_id === currentUserId;
                  
                  return (
                    <div
                      key={message.id}
                      className={`flex mb-4 ${isOwn ? 'justify-end' : 'justify-start'}`}
                    >
                      <div className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                        isOwn
                          ? 'bg-blue-600 text-white'
                          : 'bg-white text-gray-800 border'
                      }`}>
                        <div className="break-words">
                          {message.message_type === 'file' ? (
                            <div className="flex items-center space-x-2">
                              <span>📎</span>
                              <span className="font-medium">{message.content}</span>
                            </div>
                          ) : message.message_type === 'appointment_update' ? (
                            <div className="flex items-center space-x-2">
                              <span>📅</span>
                              <span className="font-medium">Appointment Update</span>
                            </div>
                          ) : (
                            <p>{message.content}</p>
                          )}
                        </div>
                        
                        <div className="flex items-center justify-between mt-2">
                          <span className={`text-xs ${
                            isOwn ? 'text-blue-100' : 'text-gray-500'
                          }`}>
                            {formatMessageTime(message.created_at)}
                          </span>
                          
                          {isOwn && (
                            <span className={`text-xs ${
                              message.is_read ? 'text-blue-100' : 'text-blue-200'
                            }`}>
                              {message.is_read ? '✓✓' : '✓'}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            ))
          )}
          
          {isTyping && (
            <div className="flex justify-start mb-4">
              <div className="bg-white text-gray-800 border px-4 py-2 rounded-lg max-w-xs">
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Message Input */}
        <form onSubmit={handleSendMessage} className="flex flex-col space-y-3">
          <div className="flex space-x-2">
            <div className="flex-1">
              <Textarea
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
                placeholder="Type your message..."
                className="resize-none"
                rows={2}
                disabled={loading}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage(e);
                  }
                }}
              />
            </div>
          </div>
          
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <input
                ref={fileInputRef}
                type="file"
                onChange={handleFileUpload}
                className="hidden"
                accept="image/*,.pdf,.doc,.docx,.txt"
                disabled={loading}
              />
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => fileInputRef.current?.click()}
                disabled={loading}
              >
                📎 Attach File
              </Button>
              
              <span className="text-xs text-gray-500">
                Press Enter to send, Shift+Enter for new line
              </span>
            </div>
            
            <Button
              type="submit"
              disabled={!newMessage.trim() || loading}
              size="sm"
            >
              {loading ? 'Sending...' : 'Send'}
            </Button>
          </div>
        </form>

        {/* HIPAA Compliance Notice */}
        <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex">
            <div className="text-blue-600 mr-2">🔒</div>
            <div className="text-sm text-blue-800">
              <p className="font-medium">Secure Messaging</p>
              <p>
                This conversation is encrypted and HIPAA-compliant. 
                Only you and your healthcare provider can access these messages.
              </p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}