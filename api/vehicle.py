import json
import re
import time
import urllib.parse
import urllib.request

# ==================== CONFIG =====================
YOUR_API_KEYS = ["GOKU"]
TARGET_API = "https://vehicleinfobyterabaap.vercel.app/lookup"
CACHE_TIME = 3600
# =================================================

cache = {}

def clean_oxmzoo(data):
    """Remove @oxmzoo from data"""
    if isinstance(data, str):
        return re.sub(r'@oxmzoo', '', data, flags=re.IGNORECASE).strip()
    if isinstance(data, list):
        return [clean_oxmzoo(item) for item in data]
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            if 'oxmzoo' not in key.lower():
                result[key] = clean_oxmzoo(value)
        return result
    return data

def handler(event, context):
    # Parse query parameters
    params = event.get('queryStringParameters', {}) or {}
    
    # Get vehicle number from multiple possible parameters
    vehicle = (
        params.get('query') or 
        params.get('vehicle') or 
        params.get('number') or 
        params.get('vehicle_number')
    )
    key = params.get('key')
    
    # Check required parameters
    if not vehicle or not key:
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json; charset=utf-8',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Missing parameters',
                'details': 'Use: ?query=CH01AC9090&key=GOKU OR ?vehicle=CH01AC9090&key=GOKU'
            })
        }
    
    # Clean and validate inputs
    vehicle = str(vehicle).strip().upper()
    key = str(key).strip()
    
    # API key validation
    if key not in YOUR_API_KEYS:
        return {
            'statusCode': 403,
            'headers': {
                'Content-Type': 'application/json; charset=utf-8',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'Invalid key'})
        }
    
    # Vehicle number format validation
    if not re.match(r'^[A-Z]{2}\d{0,4}[A-Z]{0,2}(/[A-Z]{1,4})?$', vehicle):
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json; charset=utf-8',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Invalid vehicle number format',
                'details': 'Format: CH01AB1234 or CH01/AB'
            })
        }
    
    # Cache check
    cache_key = vehicle
    now = time.time()
    
    if cache_key in cache:
        cached = cache[cache_key]
        if now - cached['time'] < CACHE_TIME:
            return {
                'statusCode': 200,
                'headers': {
                    'X-Proxy-Cache': 'HIT',
                    'Content-Type': 'application/json; charset=utf-8',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': cached['data']
            }
    
    # Make API request
    try:
        encoded_vehicle = urllib.parse.quote(vehicle)
        url = f"{TARGET_API}?query={encoded_vehicle}"
        
        req = urllib.request.Request(
            url,
            headers={
                'Accept': 'application/json',
                'User-Agent': 'Mozilla/5.0'
            }
        )
        
        with urllib.request.urlopen(req, timeout=30) as response:
            raw_data = response.read().decode('utf-8')
            
            if response.status != 200:
                return {
                    'statusCode': 502,
                    'headers': {
                        'Content-Type': 'application/json; charset=utf-8',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'error': 'Upstream API error',
                        'details': f"Status: {response.status}"
                    })
                }
            
            # Process response
            try:
                data = json.loads(raw_data)
            except:
                # If not JSON, return cleaned text
                cleaned = re.sub(r'@oxmzoo', '', raw_data, flags=re.IGNORECASE).strip()
                result = cleaned
            else:
                # Clean @oxmzoo
                data = clean_oxmzoo(data)
                
                # Add your branding
                data['developer'] = "@gokuuuu_1"
                data['credit_by'] = "goku"
                data['powered_by'] = "goku-info-api"
                
                result = json.dumps(data)
            
            # Cache the result
            cache[cache_key] = {
                'time': now,
                'data': result
            }
            
            # Clean old cache
            if len(cache) > 1000:
                # Remove oldest
                oldest = min(cache.keys(), key=lambda k: cache[k]['time'])
                del cache[oldest]
            
            return {
                'statusCode': 200,
                'headers': {
                    'X-Proxy-Cache': 'MISS',
                    'Content-Type': 'application/json; charset=utf-8',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': result
            }
    
    except urllib.error.HTTPError as e:
        return {
            'statusCode': 502,
            'headers': {
                'Content-Type': 'application/json; charset=utf-8',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'HTTP Error',
                'details': f"Code: {e.code}"
            })
        }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json; charset=utf-8',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Internal error',
                'details': str(e)
            })
        }
