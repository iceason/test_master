import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'TestCaseGenerator.settings')
django.setup()

from api.models import Directory
from api.serializers import DirectorySerializer

# Clean db
Directory.objects.all().delete()

# Create data
root = Directory.objects.create(name="Root")
child = Directory.objects.create(name="Child", parent=root)
grandchild = Directory.objects.create(name="GrandChild", parent=child)

try:
    # Serialize
    serializer = DirectorySerializer(instance=root)
    print("Root Data:", serializer.data)

    # Serialize List
    serializer_list = DirectorySerializer(instance=[root], many=True)
    print("List Data:", serializer_list.data)
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
