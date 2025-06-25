import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  Box,
  Flex,
  Input,
  IconButton,
  Text,
  Avatar,
  Checkbox,
  Button,
  ChakraProvider,
} from '@chakra-ui/react';
import { FiSend } from "react-icons/fi";
import { FaUserTie } from "react-icons/fa";
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import './ChatBubbles.css';

function App() {
  const [messages, setMessages] = useState([]); // Message history
  const messagesRef = useRef(messages); // Ref to hold the latest messages
  const abortControllerRef = useRef(null); // Ref to manage the abort controller for canceling requests

  useEffect(() => {
    messagesRef.current = messages; // Update messagesRef on message state change
  }, [messages]);

  const [userMessage, setUserMessage] = useState("");
  const [pendingMessage, setPendingMessage] = useState(null);
  const [activeAgents, setActiveAgents] = useState([]); // Now dynamic
  const [agentList, setAgentList] = useState([]); // To load from the backend

  useEffect(() => {
    async function fetchAgents() {
      try {
        const response = await axios.get("http://localhost:8000/bots");
        setAgentList(response.data);
        setActiveAgents(response.data.map(agent => agent.name)); // Activate all agents by default
      } catch (error) {
        console.error("Error fetching agent list:", error);
      }
    }
    fetchAgents();
  }, []);
  
  // Function to handle agent selection
  const toggleAgent = (agentName) => {
    setActiveAgents((prevActiveAgents) => {
      if (prevActiveAgents.includes(agentName)) {
        return prevActiveAgents.filter((name) => name !== agentName);
      } else {
        return [...prevActiveAgents, agentName];
      }
    });
  };

  // Function to clear the conversation and stop agent responses
  const clearConversation = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    setMessages([]);
  };

  // Function to send message to backend
  const sendMessageToBackend = useCallback(async () => {
    if (!pendingMessage) return; // Prevent running if there's no pending message

    try {
      abortControllerRef.current = new AbortController(); // Initialize the abort controller
      const signal = abortControllerRef.current.signal;

      // Use messagesRef.current to get the latest messages
      const response = await axios.post(
        "http://localhost:8000/chat",
        {
          text: pendingMessage.text,
          conversation_history: messagesRef.current,
          active_bots: activeAgents,
        },
        { signal }
      );

      const agentResponses = response.data.responses;

      for (let i = 0; i < agentResponses.length; i++) {
        const agentResponse = agentResponses[i];
        await new Promise((resolve) => setTimeout(resolve, 2000));

        setMessages((prevMessages) => [
          ...prevMessages,
          {
            speaker: agentResponse.bot,
            text: agentResponse.response,
          },
        ]);
      }
    } catch (error) {
      if (axios.isCancel(error)) {
        console.log("Agent response generation was canceled");
      } else {
        console.error("Error sending message:", error);
      }
    } finally {
      setPendingMessage(null);
      abortControllerRef.current = null;
    }
  }, [pendingMessage, activeAgents]);

  useEffect(() => {
    sendMessageToBackend();
  }, [pendingMessage, sendMessageToBackend]);

  // Function to send a message
  const handleSendMessage = () => {
    if (userMessage.trim() === "") return;

    const newMessage = {
      speaker: "User",
      text: userMessage,
    };

    setMessages((prevMessages) => [...prevMessages, newMessage]);
    setUserMessage("");
    setPendingMessage(newMessage);
  };

  // Use a generic avatar for each agent (initials or icon)
  const getAgentAvatar = (agentName) => {
    // Use initials
    const initials = agentName.split(' ').map(w => w[0]).join('').toUpperCase();
    return <Avatar icon={<FaUserTie />} name={agentName} size="md" bg="teal.500" color="white">{initials}</Avatar>;
  };

  const chatContainerStyle = {
    height: '100%',
    position: 'relative',
    display: 'flex',
    flexDirection: 'column',
    paddingBottom: '20px',
    overflow: 'hidden',
    zIndex: 2,
  };

  const pseudoElementStyle = {
    content: '""',
    position: 'absolute',
    top: 0,
    left: 0,
    width: '100%',
    height: '100%',
    background: '#111',
    backgroundSize: 'cover',
    backgroundPosition: 'center',
    backgroundRepeat: 'no-repeat',
    opacity: 1,
    zIndex: -1,
  };

  return (
    <Flex direction="row" h="100vh" w="100vw" backgroundColor="gray.900">
      {/* Left Panel for Agent Selection */}
      <Box w="320px" backgroundColor="black" p={4} color="white" position="relative">
        <Text mb={4} fontSize="xl" fontWeight="bold">Select Agents:</Text>
        {agentList.map((agent, index) => (
          <Flex key={index} className="agent-selection" alignItems="flex-start" position="relative" mb={4}>
              <Checkbox
              isChecked={activeAgents.includes(agent.name)}
              onChange={() => toggleAgent(agent.name)}
              colorScheme="teal"
              size="lg"
              mr={3}
            />
            {getAgentAvatar(agent.name)}
            <Box ml={3}>
              <Text fontWeight="bold">{agent.name}</Text>
              <Text fontSize="sm" color="gray.300">{agent.role}</Text>
            </Box>
          </Flex>
        ))}
        {/* New Conversation Button */}
        <Flex 
          position="absolute" 
          bottom="10px"
          width="100%" 
          px={4} 
          justifyContent="flex-start"
          left="40px"
          zIndex="1"
        >
          <Button 
            onClick={clearConversation} 
            bg="white"
            color="black"
            borderRadius="20px"  
            padding="10px"
            width="50%"
            _hover={{
              bg: "#f0f0f0"
            }}
          >
            New
          </Button>
        </Flex>
      </Box>

      {/* Chat Container */}
      <Flex direction="column" flex="1" overflow="hidden">
        <Box className="chat-container" style={chatContainerStyle}>
          {/* Pseudo-element for background */}
          <Box style={pseudoElementStyle}></Box>

          <Box className="messages-container" flex="1" overflowY="auto" padding="20px">
          {messages.map((msg, index) => {
            return (
              <Flex
                key={index}
                justifyContent={msg.speaker === "User" ? "flex-end" : "flex-start"}
                maxW="100%"
                mb={4}
                alignItems="flex-end"
              >
                {msg.speaker !== "User" ? (
                  <Flex alignItems="flex-end">
                    {getAgentAvatar(msg.speaker)}
                    <Box className={`message bot`} data-name={msg.speaker} ml={2}>
                      <ReactMarkdown>{msg.text}</ReactMarkdown>
                    </Box>
                  </Flex>
                ) : (
                  <Box className={`message user`}>
                    <Text>{msg.text}</Text>
                  </Box>
                )}
              </Flex>
            );
          })}
          </Box>

          <Flex
            className="input-container"
            mt={4}
            px={4}
            align="center"
            position="absolute"
            bottom="0"
            width="100%"
            backgroundColor="white"
            padding="10px"
            borderTop="1px solid #e5e5e5"
          >
            <Input
              placeholder="Type your message..."
              value={userMessage}
              onChange={(e) => setUserMessage(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  handleSendMessage();
                }
              }}
              flex={1}
              bg="gray.100"
              color="black"
              borderRadius="20px"
              mr={2}
              px={4}
            />
            <IconButton
              onClick={handleSendMessage}
              icon={<FiSend size={20} />}
              aria-label="Send message"
              className="send-button"
            />
          </Flex>
        </Box>
      </Flex>
    </Flex>
  );
}

export default App;