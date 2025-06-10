require('dotenv').config();
const express = require('express');
const axios = require('axios');
const config = require('./config/bot-config.json');

const app = express();
app.use(express.json());

// Basic health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});

// Main webhook endpoint
app.post('/webhook', async (req, res) => {
  try {
    // Process incoming webhook
    const response = await processWebhook(req.body);
    res.json(response);
  } catch (error) {
    console.error('Error processing webhook:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

async function processWebhook(payload) {
  // TODO: Implement webhook processing logic
  return { success: true };
}

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
