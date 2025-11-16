
import anthropic
import base64
import json
import os
import re

def floorplan_png_to_json(png_path, api_key, output_path=None):
    """
    Convert a floor plan PNG to structured JSON with walls and rooms.
    
    Args:
        png_path: Path to the floor plan PNG file
        api_key: Your Anthropic API key
        output_path: Optional path for output JSON file
    
    Returns:
        dict: JSON with walls (with coordinates) and rooms (with center points)
    """
    
    # Read and encode the PNG file
    with open(png_path, 'rb') as image_file:
        image_data = base64.standard_b64encode(image_file.read()).decode('utf-8')
    
    # Initialize the Anthropic client
    client = anthropic.Anthropic(api_key=api_key)
    
    # Craft a detailed prompt for floor plan analysis
    prompt = """Analyze this floor plan image and extract the architectural data in the following JSON format:

{
  "walls": [
    {
      "wall_id": "wall_1",
      "start_point": {"x": <float>, "y": <float>},
      "end_point": {"x": <float>, "y": <float>}
    }
  ],
  "rooms": [
    {
      "room_name": "<ROOM_TYPE>",
      "center_point": {"x": <float>, "y": <float>}
    }
  ]
}

Instructions:
1. Identify all walls and their start/end coordinates
2. Identify all rooms and their center points
3. Use appropriate room names (BEDROOM, KITCHEN, BATHROOM, LIVING ROOM, etc.)
4. Provide coordinates with decimal precision (e.g., 32.66399064)
5. Return ONLY the JSON structure, no additional text
6. Ensure all walls are numbered sequentially (wall_1, wall_2, etc.)"""
    
    # Send the image to Claude for analysis
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": image_data,
                        },
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ],
            }
        ],
    )
    
    # Extract the response text
    response_text = message.content[0].text
    
    # Remove markdown code blocks if present
    response_text = re.sub(r'```json\s*|\s*```', '', response_text).strip()
    
    # Parse the JSON
    try:
        result = json.loads(response_text)
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON: {e}")
        print(f"Raw response: {response_text}")
        # Create a fallback structure
        result = {
            "walls": [],
            "rooms": [],
            "error": "Failed to parse response",
            "raw_response": response_text
        }
    
    # Save to file if output path is provided
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"JSON saved to: {output_path}")
    
    return result


def png_to_json_with_base64(png_path, output_path=None):
    """
    Convert PNG directly to JSON with base64 encoding (no API call).
    
    Args:
        png_path: Path to the PNG file
        output_path: Optional path for output JSON file
    
    Returns:
        dict: JSON with image metadata and base64 data
    """
    
    # Read and encode the PNG file
    with open(png_path, 'rb') as image_file:
        image_data = base64.standard_b64encode(image_file.read()).decode('utf-8')
    
    # Get file info
    file_size = os.path.getsize(png_path)
    
    # Create JSON structure
    result = {
        "filename": os.path.basename(png_path),
        "path": png_path,
        "size_bytes": file_size,
        "media_type": "image/png",
        "encoding": "base64",
        "data": image_data
    }
    
    # Save to file if output path is provided
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
        print(f"JSON saved to: {output_path}")
    
    return result


# Example usage
if __name__ == "__main__":
    # Replace with your actual API key
    # API_KEY = "your-api-key-here"
    API_KEY = "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"

    # Convert floor plan PNG to structured JSON
    result = floorplan_png_to_json(
        png_path="floorplan.png",
        api_key=API_KEY,
        output_path="floorplan_output.json"
    )
    
    print("Conversion complete!")
    print(f"Found {len(result.get('walls', []))} walls")
    print(f"Found {len(result.get('rooms', []))} rooms")
    
    # Display sample data
    if result.get('walls'):
        print(f"\nFirst wall: {result['walls'][0]}")
    if result.get('rooms'):
        print(f"First room: {result['rooms'][0]}")