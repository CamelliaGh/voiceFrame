#!/bin/bash

echo "🚀 Setting up VoiceFrame monitoring stack..."

# Create monitoring directory if it doesn't exist
mkdir -p monitoring/grafana/provisioning/datasources
mkdir -p monitoring/grafana/provisioning/dashboards
mkdir -p monitoring/grafana/dashboards

# Start monitoring stack
echo "📊 Starting Prometheus and Grafana..."
cd monitoring
docker-compose -f docker-compose.monitoring.yml up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check if services are running
echo "🔍 Checking service status..."
docker-compose -f docker-compose.monitoring.yml ps

echo ""
echo "✅ Monitoring stack is ready!"
echo ""
echo "📊 Access your monitoring tools:"
echo "   • Grafana: http://localhost:3001 (admin/admin123)"
echo "   • Prometheus: http://localhost:9090"
echo "   • cAdvisor: http://localhost:8080"
echo "   • Node Exporter: http://localhost:9100/metrics"
echo ""
echo "🎯 VoiceFrame metrics: http://localhost:8000/metrics"
echo ""
echo "📈 Grafana dashboards:"
echo "   • VoiceFrame Overview: http://localhost:3001/d/voiceframe-overview"
echo ""
echo "🔔 Alerts are configured for:"
echo "   • High disk usage (>90%)"
echo "   • High memory usage (>90%)"
echo "   • Container restarts"
echo "   • API downtime"
echo "   • High error rates"
echo ""
echo "💡 To stop monitoring: docker-compose -f monitoring/docker-compose.monitoring.yml down"
