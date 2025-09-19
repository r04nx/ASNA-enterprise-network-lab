#!/bin/bash
echo "🌐 Starting continuous network traffic generation..."
echo "Press Ctrl+C to stop"

# Function to generate traffic between random devices
generate_traffic() {
    containers=($(docker ps --format "{{.Names}}" | grep clab-enterprise-final))
    
    while true; do
        # Pick two random containers
        src_container=${containers[$RANDOM % ${#containers[@]}]}
        dst_container=${containers[$RANDOM % ${#containers[@]}]}
        
        if [ "$src_container" != "$dst_container" ]; then
            dst_ip=$(docker inspect $dst_container | jq -r '.[0].NetworkSettings.Networks[].IPAddress')
            
            # Generate different types of traffic
            case $((RANDOM % 4)) in
                0) 
                    # Ping traffic
                    docker exec $src_container ping -c 2 $dst_ip >/dev/null 2>&1 &
                    ;;
                1)
                    # HTTP-like traffic (if containers support it)
                    docker exec $src_container wget --timeout=2 -q -O /dev/null http://$dst_ip:80 2>/dev/null &
                    ;;
                2)
                    # Generate some data transfer
                    docker exec $src_container sh -c "echo 'test data traffic' | nc -w 1 $dst_ip 1234" >/dev/null 2>&1 &
                    ;;
                3)
                    # DNS-like traffic
                    docker exec $src_container nslookup google.com >/dev/null 2>&1 &
                    ;;
            esac
        fi
        
        sleep $((1 + RANDOM % 3))  # Random interval between 1-4 seconds
    done
}

# Handle Ctrl+C
trap 'echo -e "\nStopping traffic generation..."; exit 0' INT

# Start traffic generation
generate_traffic
