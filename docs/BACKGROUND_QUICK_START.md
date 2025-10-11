# Background Management - Quick Start

## TL;DR

All backgrounds are now managed through the **Admin Panel** instead of being hardcoded! 🎉

## What You Need to Do

### 1. Run Migration Script (One-Time)

This adds your existing backgrounds to the database.

**If using Docker (recommended):**

```bash
docker-compose exec api python3 -c "
import sys, os
from backend.database import SessionLocal
from backend.models import AdminBackground
import uuid

db = SessionLocal()
backgrounds = [
    {'name': 'abstract-blurred', 'display_name': 'Abstract Blurred', 'description': 'Soft abstract background', 'category': 'Abstract', 'file_path': 'backgrounds/237.jpg', 'orientation': 'both'},
    {'name': 'roses-wooden', 'display_name': 'Roses & Wood', 'description': 'Beautiful roses on wooden background', 'category': 'Romantic', 'file_path': 'backgrounds/beautiful-roses-great-white-wooden-background-with-space-right.jpg', 'orientation': 'both'},
    {'name': 'cute-hearts', 'display_name': 'Cute Hearts', 'description': 'Romantic hearts background', 'category': 'Romantic', 'file_path': 'backgrounds/copy-space-with-cute-hearts.jpg', 'orientation': 'both'},
    {'name': 'flat-lay-hearts', 'display_name': 'Flat Lay Hearts', 'description': 'Elegant flat lay hearts', 'category': 'Romantic', 'file_path': 'backgrounds/flat-lay-small-cute-hearts.jpg', 'orientation': 'both'}
]

count = 0
for bg in backgrounds:
    existing = db.query(AdminBackground).filter(AdminBackground.name == bg['name']).first()
    if existing:
        print(f\"Skip: {bg['name']} exists\")
        continue
    file_size = os.path.getsize(bg['file_path']) if os.path.exists(bg['file_path']) else None
    background = AdminBackground(id=str(uuid.uuid4()), name=bg['name'], display_name=bg['display_name'], description=bg['description'], category=bg['category'], file_path=bg['file_path'], file_size=file_size, orientation=bg['orientation'], is_premium=False, is_active=True, usage_count=0)
    db.add(background)
    print(f\"Added: {bg['name']}\")
    count += 1
db.commit()
db.close()
print(f\"Done! Migrated {count} backgrounds\")
"
```

**If running locally without Docker:**

```bash
source venv/bin/activate
python3 scripts/migrate_backgrounds_to_admin.py
```

### 2. Verify Migration Success

You should see output like:
```
Added: abstract-blurred
Added: roses-wooden
Added: cute-hearts
Added: flat-lay-hearts
Done! Migrated 4 backgrounds
```

### 3. Verify in Admin Panel

1. Go to `/admin`
2. Click "Backgrounds" section
3. Verify your backgrounds appear
4. All should be marked as "Active"

### 4. Test Everything Works

1. Go to customization panel
2. Switch PDF orientations (portrait/landscape)
3. Select different backgrounds
4. Generate a preview PDF
5. Verify background appears correctly

## Adding New Backgrounds

From now on, to add a new background:

1. **Go to Admin Panel** → Backgrounds
2. **Click "Add Background"**
3. **Fill in**:
   - Name: `sunset-beach` (lowercase-with-hyphens)
   - Display Name: `Sunset Beach`
   - Description: `Beautiful sunset over beach`
   - Category: `Nature`, `Romantic`, `Abstract`, etc.
   - Orientation: `portrait`, `landscape`, or `both`
4. **Upload the image file**
5. **Click Save**

Done! The background is immediately available in the app.

## Benefits

✅ No code changes needed to add/remove backgrounds
✅ Backgrounds filter by PDF orientation automatically
✅ Can mark backgrounds as premium
✅ Can temporarily disable backgrounds without deleting
✅ Track usage statistics
✅ Organize with categories

## Troubleshooting

**Background not showing?**
- Check it's marked "Active" in admin panel
- Verify orientation matches (portrait/landscape/both)
- Clear browser cache

**Background not in PDF?**
- Verify file exists at stored path
- Check backend logs for errors
- Restart backend server

## More Details

- **Full Guide**: [BACKGROUND_MIGRATION_GUIDE.md](./BACKGROUND_MIGRATION_GUIDE.md)
- **Technical Details**: [BACKGROUND_PATH_FIX.md](./BACKGROUND_PATH_FIX.md)
