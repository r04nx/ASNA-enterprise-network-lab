#!/bin/bash

# AI Dashboard Import Script for ASNA
# This script creates/updates Grafana dashboard with AI agent metrics

echo "🤖 Setting up AI Agent Performance Dashboard..."

# Wait for Grafana to be ready
echo "⏳ Waiting for Grafana to be available..."
for i in {1..30}; do
    if curl -s http://admin:asna123@localhost:3000/api/health > /dev/null 2>&1; then
        echo "✅ Grafana is ready"
        break
    fi
    echo "   Attempt $i/30 - waiting for Grafana..."
    sleep 2
done

# Create AI Performance Dashboard via API
echo "📊 Creating AI Agent Performance Dashboard..."

curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "dashboard": {
      "id": null,
      "title": "🤖 ASNA - AI Agent Performance",
      "tags": ["ASNA", "AI", "self-healing", "reinforcement-learning"],
      "timezone": "browser",
      "panels": [
        {
          "id": 1,
          "title": "🧠 AI Confidence Score",
          "type": "gauge",
          "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
          "targets": [
            {
              "expr": "selfheal_ai_confidence_score",
              "legendFormat": "AI Confidence - {{device}}"
            }
          ],
          "fieldConfig": {
            "defaults": {
              "unit": "percentunit",
              "min": 0,
              "max": 1,
              "thresholds": {
                "steps": [
                  {"color": "red", "value": 0},
                  {"color": "yellow", "value": 0.5},
                  {"color": "green", "value": 0.8}
                ]
              }
            }
          }
        },
        {
          "id": 2,
          "title": "📊 AI Decisions Over Time",
          "type": "timeseries",
          "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
          "targets": [
            {
              "expr": "selfheal_ai_decisions_total",
              "legendFormat": "Total Decisions - {{device}}"
            },
            {
              "expr": "selfheal_ai_successful_decisions_total",
              "legendFormat": "Successful Decisions - {{device}}"
            }
          ]
        },
        {
          "id": 3,
          "title": "🔍 Exploration vs Exploitation",
          "type": "timeseries",
          "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8},
          "targets": [
            {
              "expr": "selfheal_ai_exploration_decisions_total",
              "legendFormat": "Exploration - {{device}}"
            },
            {
              "expr": "selfheal_ai_exploitation_decisions_total",
              "legendFormat": "Exploitation - {{device}}"
            }
          ]
        },
        {
          "id": 4,
          "title": "📚 AI Learning Progress",
          "type": "timeseries",
          "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8},
          "targets": [
            {
              "expr": "selfheal_ai_learning_updates_total",
              "legendFormat": "Learning Updates - {{device}}"
            },
            {
              "expr": "rate(selfheal_ai_learning_updates_total[5m])",
              "legendFormat": "Learning Rate/sec - {{device}}"
            }
          ]
        },
        {
          "id": 5,
          "title": "📈 AI Summary Statistics",
          "type": "stat",
          "gridPos": {"h": 6, "w": 24, "x": 0, "y": 16},
          "targets": [
            {
              "expr": "selfheal_ai_decisions_total",
              "legendFormat": "Total Decisions"
            },
            {
              "expr": "selfheal_ai_successful_decisions_total",
              "legendFormat": "Successful"
            },
            {
              "expr": "selfheal_ai_learning_updates_total",
              "legendFormat": "Learning Updates"
            },
            {
              "expr": "selfheal_ai_confidence_score * 100",
              "legendFormat": "Confidence %"
            }
          ]
        }
      ],
      "time": {
        "from": "now-1h",
        "to": "now"
      },
      "refresh": "5s"
    },
    "overwrite": true
  }' \
  http://admin:asna123@localhost:3000/api/dashboards/db

echo ""
echo "✅ AI Agent Performance Dashboard created successfully!"
echo "🌐 Access it at: http://localhost:3000"
echo "📊 Look for: '🤖 ASNA - AI Agent Performance' dashboard"
echo ""
