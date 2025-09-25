"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Message, PatientProfile, DoctorProfile } from "@/types";

interface Conversation {
  recipientId: string;
  recipient: PatientProfile | DoctorProfile;
  lastMessage?: Message;
  unreadCount: number;
  lastActivity: string;
}

interface ConversationListProps {
  conversations: Conversation[];
  currentUserId: string;
  currentUserType: 'patient' | 'doctor';
  onSelectConversation: (conversation: Conversation) => void;
  onStartNewConversation?: () => void;
  selectedConversationId?: string;
}

export function ConversationList({
  conversations,
  currentUserId,
  currentUserType,
  onSelectConversation,
  onStartNewConversation,
  selectedConversationId
}: ConversationListProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [filter, setFilter] = useState<'all' | 'unread' | 'recent'>('all');

  const formatLastMessageTime = (dateString: string) => {
    const messageDate = new Date(dateString);
    const now = new Date();
    const diffInHours = (now.getTime() - messageDate.getTime()) / (1000 * 60 * 60);

    if (diffInHours < 1) {
      const diffInMinutes = Math.floor(diffInHours * 60);
      return diffInMinutes < 1 ? 'Just now' : `${diffInMinutes}m ago`;
    } else if (diffInHours < 24) {
      return `${Math.floor(diffInHours)}h ago`;
    } else if (diffInHours < 24 * 7) {
      const diffInDays = Math.floor(diffInHours / 24);
      return `${diffInDays}d ago`;
    } else {
      return messageDate.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric'
      });
    }
  };

  const getRecipientName = (recipient: PatientProfile | DoctorProfile) => {
    return `${recipient.first_name} ${recipient.last_name}`;
  };

  const getRecipientSubtitle = (recipient: PatientProfile | DoctorProfile) => {
    if (currentUserType === 'patient') {
      return `Dr. ${recipient.last_name} - ${(recipient as DoctorProfile).specialization}`;
    } else {
      return `@${(recipient as PatientProfile).username}`;
    }
  };

  const truncateMessage = (content: string, maxLength: number = 50) => {
    if (content.length <= maxLength) return content;
    return content.substring(0, maxLength) + '...';
  };

  const filteredConversations = conversations
    .filter(conversation => {
      // Search filter
      if (searchTerm) {
        const name = getRecipientName(conversation.recipient).toLowerCase();
        const searchLower = searchTerm.toLowerCase();
        
        if (!name.includes(searchLower)) {
          return false;
        }
      }

      // Status filter
      switch (filter) {
        case 'unread':
          return conversation.unreadCount > 0;
        case 'recent':
          const lastActivity = new Date(conversation.lastActivity);
          const dayAgo = new Date(Date.now() - 24 * 60 * 60 * 1000);
          return lastActivity > dayAgo;
        default:
          return true;
      }
    })
    .sort((a, b) => {
      // Sort by last activity, most recent first
      return new Date(b.lastActivity).getTime() - new Date(a.lastActivity).getTime();
    });

  const totalUnreadCount = conversations.reduce((sum, conv) => sum + conv.unreadCount, 0);

  return (
    <Card className="w-full max-w-md h-[600px] flex flex-col">
      <CardHeader className="shrink-0">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Messages</CardTitle>
            <CardDescription>
              {totalUnreadCount > 0 && `${totalUnreadCount} unread message${totalUnreadCount !== 1 ? 's' : ''}`}
            </CardDescription>
          </div>
          {onStartNewConversation && (
            <Button onClick={onStartNewConversation} size="sm">
              New
            </Button>
          )}
        </div>
      </CardHeader>

      <CardContent className="flex-1 flex flex-col min-h-0">
        {/* Search and Filter */}
        <div className="space-y-3 mb-4">
          <Input
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder={`Search ${currentUserType === 'patient' ? 'doctors' : 'patients'}...`}
            className="w-full"
          />
          
          <div className="flex space-x-2">
            {[
              { value: 'all', label: 'All' },
              { value: 'unread', label: 'Unread' },
              { value: 'recent', label: 'Recent' }
            ].map((option) => (
              <Button
                key={option.value}
                variant={filter === option.value ? "default" : "outline"}
                size="sm"
                onClick={() => setFilter(option.value as any)}
                className="flex-1"
              >
                {option.label}
                {option.value === 'unread' && totalUnreadCount > 0 && (
                  <span className="ml-1 bg-red-500 text-white rounded-full text-xs px-1.5 py-0.5">
                    {totalUnreadCount}
                  </span>
                )}
              </Button>
            ))}
          </div>
        </div>

        {/* Conversations List */}
        <div className="flex-1 overflow-y-auto space-y-2">
          {filteredConversations.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              {conversations.length === 0 ? (
                <div>
                  <p>No conversations yet</p>
                  {onStartNewConversation && (
                    <Button 
                      variant="outline" 
                      size="sm" 
                      className="mt-2"
                      onClick={onStartNewConversation}
                    >
                      Start your first conversation
                    </Button>
                  )}
                </div>
              ) : (
                <p>No conversations match your search</p>
              )}
            </div>
          ) : (
            filteredConversations.map((conversation) => (
              <div
                key={conversation.recipientId}
                onClick={() => onSelectConversation(conversation)}
                className={`p-3 rounded-lg cursor-pointer transition-colors ${
                  selectedConversationId === conversation.recipientId
                    ? 'bg-blue-50 border-blue-200 border'
                    : 'hover:bg-gray-50 border border-transparent'
                }`}
              >
                <div className="flex items-start space-x-3">
                  {/* Avatar placeholder */}
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-400 to-blue-600 flex items-center justify-center text-white font-medium">
                    {conversation.recipient.first_name[0]}{conversation.recipient.last_name[0]}
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <h3 className="font-medium text-sm truncate">
                        {getRecipientName(conversation.recipient)}
                      </h3>
                      <div className="flex items-center space-x-2">
                        {conversation.unreadCount > 0 && (
                          <span className="bg-blue-500 text-white rounded-full text-xs px-2 py-1 min-w-[20px] text-center">
                            {conversation.unreadCount}
                          </span>
                        )}
                        <span className="text-xs text-gray-500">
                          {formatLastMessageTime(conversation.lastActivity)}
                        </span>
                      </div>
                    </div>

                    <p className="text-xs text-gray-600 mb-1">
                      {getRecipientSubtitle(conversation.recipient)}
                    </p>

                    {conversation.lastMessage && (
                      <div className="flex items-center space-x-1">
                        {conversation.lastMessage.sender_id === currentUserId && (
                          <span className="text-xs text-gray-400">
                            {conversation.lastMessage.is_read ? '✓✓' : '✓'}
                          </span>
                        )}
                        <p className={`text-xs truncate ${
                          conversation.unreadCount > 0 && conversation.lastMessage.sender_id !== currentUserId
                            ? 'font-medium text-gray-900'
                            : 'text-gray-500'
                        }`}>
                          {conversation.lastMessage.message_type === 'file' ? (
                            <span>📎 Sent a file</span>
                          ) : conversation.lastMessage.message_type === 'appointment_update' ? (
                            <span>📅 Appointment update</span>
                          ) : (
                            truncateMessage(conversation.lastMessage.content)
                          )}
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Status indicator */}
        <div className="mt-4 pt-3 border-t">
          <div className="flex items-center justify-center space-x-2 text-sm text-gray-500">
            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
            <span>Secure messaging enabled</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}