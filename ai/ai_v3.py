import anthropic
import base64
import json
import os
import re
from dotenv import load_dotenv
from typing import Optional, Dict, List


def floorplan_png_to_json(png_path: str, api_key: Optional[str] = None, output_path: Optional[str] = None) -> Dict:
    """
    Convert a floor plan PNG to structured JSON with walls and rooms.

    Args:
        png_path: Path to the floor plan PNG file
        api_key: Your Anthropic API key (optional if set in environment)
        output_path: Optional path for output JSON file

    Returns:
        dict: JSON with walls (with coordinates) and rooms (with center points)
    """

    # Load environment variables and get API key
    load_dotenv()
    api_key = api_key or os.getenv('ANTHROPIC_API_KEY')

    if not api_key:
        raise ValueError(
            "API key not found. Please set ANTHROPIC_API_KEY environment variable "
            "or pass api_key parameter."
        )

    # Validate input file
    if not os.path.exists(png_path):
        raise FileNotFoundError(f"Floor plan image not found: {png_path}")

    # Read and encode the PNG file
    with open(png_path, 'rb') as image_file:
        image_data = base64.standard_b64encode(image_file.read()).decode('utf-8')

    # Initialize the Anthropic client
    client = anthropic.Anthropic(api_key=api_key)

    # Enhanced prompt for accurate floor plan extraction
    prompt = """Analyze this floor plan image and extract ALL architectural elements in the following EXACT JSON format:

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

CRITICAL INSTRUCTIONS FOR WALLS:
1. Identify EVERY wall segment, including:
   - Exterior perimeter walls
   - Interior partition walls
   - Short wall segments around doorways
   - Walls around fixtures (closets, bathrooms)
2. Break walls at ALL intersections (T-junctions, corners, doorways)
3. Each wall segment should have sequential numbering (wall_1, wall_2, wall_3, etc.)
4. Provide precise floating-point coordinates with high precision (e.g., 32.45638053)
5. IGNORE the following (do NOT treat as walls):
   - Red text/dimensions
   - Green lines (doors)
   - Magenta lines (dimension lines)
   - Furniture or fixtures drawn in the plan

CRITICAL INSTRUCTIONS FOR ROOMS:
1. Identify all distinct rooms/spaces
2. Use standard room names: OFFICE, BEDROOM, BED, BATH, BATHROOM, KITCHEN, LIVING ROOM, DINING ROOM, CLOSET, HALLWAY, etc.
3. Provide the geometric center point of each room
4. Use high-precision floating-point coordinates

OUTPUT REQUIREMENTS:
- Return ONLY valid JSON, no markdown formatting, no explanation
- Ensure proper JSON structure with correct brackets and commas
- Use decimal precision for all coordinates (minimum 8 decimal places)
- Number walls sequentially without gaps

Before finalizing, verify:
✓ All visible walls are captured
✓ All rooms are identified
✓ JSON is valid and complete"""

    try:
        # Send the image to Claude for analysis
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=8192,  # Increased for larger floor plans
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

        # Clean up the response
        response_text = clean_json_response(response_text)

        # Parse the JSON
        result = json.loads(response_text)

        # Validate the structure
        result = validate_and_fix_structure(result)

    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse JSON: {e}")
        print(f"Raw response preview: {response_text[:500]}...")
        result = {
            "walls": [],
            "rooms": [],
            "error": f"Failed to parse response: {str(e)}",
            "raw_response": response_text
        }
    except Exception as e:
        print(f"❌ Error during API call: {e}")
        result = {
            "walls": [],
            "rooms": [],
            "error": f"API error: {str(e)}"
        }

    # Save to file if output path is provided
    if output_path:
        save_json_output(result, output_path)

    # Print summary
    print_summary(result)

    return result


def clean_json_response(response_text: str) -> str:
    """Remove markdown code blocks and clean up the JSON response."""
    # Remove markdown code blocks
    response_text = re.sub(r'```json\s*|\s*```', '', response_text)
    response_text = re.sub(r'```\s*', '', response_text)

    # Remove any leading/trailing whitespace
    response_text = response_text.strip()

    # Find the first { and last } to extract just the JSON
    first_brace = response_text.find('{')
    last_brace = response_text.rfind('}')

    if first_brace != -1 and last_brace != -1:
        response_text = response_text[first_brace:last_brace + 1]

    return response_text


def validate_and_fix_structure(data: Dict) -> Dict:
    """Validate and fix the structure to match the required schema."""

    # Ensure top-level keys exist
    if 'walls' not in data:
        data['walls'] = []
    if 'rooms' not in data:
        data['rooms'] = []

    # Validate walls structure
    validated_walls = []
    for i, wall in enumerate(data.get('walls', []), 1):
        if not isinstance(wall, dict):
            continue

        validated_wall = {
            'wall_id': wall.get('wall_id', f'wall_{i}'),
            'start_point': {
                'x': float(wall.get('start_point', {}).get('x', 0)),
                'y': float(wall.get('start_point', {}).get('y', 0))
            },
            'end_point': {
                'x': float(wall.get('end_point', {}).get('x', 0)),
                'y': float(wall.get('end_point', {}).get('y', 0))
            }
        }
        validated_walls.append(validated_wall)

    # Validate rooms structure
    validated_rooms = []
    for room in data.get('rooms', []):
        if not isinstance(room, dict):
            continue

        validated_room = {
            'room_name': room.get('room_name', 'UNKNOWN').upper(),
            'center_point': {
                'x': float(room.get('center_point', {}).get('x', 0)),
                'y': float(room.get('center_point', {}).get('y', 0))
            }
        }
        validated_rooms.append(validated_room)

    return {
        'walls': validated_walls,
        'rooms': validated_rooms
    }


def save_json_output(data: Dict, output_path: str) -> None:
    """Save the JSON data to a file with proper formatting."""
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"✅ JSON saved to: {output_path}")
    except Exception as e:
        print(f"❌ Failed to save JSON: {e}")


def print_summary(data: Dict) -> None:
    """Print a summary of the extracted floor plan data."""
    print("\n" + "=" * 50)
    print("FLOOR PLAN EXTRACTION SUMMARY")
    print("=" * 50)

    walls = data.get('walls', [])
    rooms = data.get('rooms', [])

    print(f"✅ Found {len(walls)} walls")
    print(f"✅ Found {len(rooms)} rooms")

    if data.get('error'):
        print(f"⚠️  Error: {data['error']}")

    # Display sample data
    if walls:
        print(f"\n📏 Sample wall (first):")
        print(f"   {json.dumps(walls[0], indent=4)}")

    if rooms:
        print(f"\n🏠 Sample room (first):")
        print(f"   {json.dumps(rooms[0], indent=4)}")

    if rooms:
        print(f"\n🏠 All rooms identified:")
        for room in rooms:
            print(f"   - {room['room_name']}")

    print("=" * 50 + "\n")


def png_to_json_with_base64(png_path: str, output_path: Optional[str] = None) -> Dict:
    """
    Convert PNG directly to JSON with base64 encoding (no API call).
    Useful for creating payloads to send to other services.

    Args:
        png_path: Path to the PNG file
        output_path: Optional path for output JSON file

    Returns:
        dict: JSON with image metadata and base64 data
    """

    if not os.path.exists(png_path):
        raise FileNotFoundError(f"Image file not found: {png_path}")

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
        save_json_output(result, output_path)

    return result


# Example usage
if __name__ == "__main__":
    # Convert floor plan PNG to structured JSON
    result = floorplan_png_to_json(
        png_path="floorplan.png",
        api_key=None,  # Will use ANTHROPIC_API_KEY from .env
        output_path="floorplan_output.json"
    )

    # Alternative: Convert PNG to base64 JSON (no API call)
    # base64_result = png_to_json_with_base64(
    #     png_path="floorplan.png",
    #     output_path="floorplan_base64.json"
    # )