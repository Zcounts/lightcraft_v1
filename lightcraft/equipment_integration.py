"""
Integration module for the LightCraft application's equipment library.
Connects equipment library with canvas and controllers.
"""

from PyQt6.QtWidgets import QVBoxLayout, QSplitter, QWidget
from PyQt6.QtCore import Qt, QPointF, QObject, pyqtSignal, pyqtSlot

from lightcraft.ui.equipment_library import EquipmentLibraryPanel
from lightcraft.ui.properties_panel import PropertiesPanel
from lightcraft.models.equipment import LightingEquipment, Camera, SetElement
from lightcraft.models.equipment_data import get_equipment_by_id


class EquipmentController(QObject):
    """
    Controller for managing equipment, bridging between the UI and data models.
    """
    
    # Signal for when equipment is selected from the library
    equipment_selected = pyqtSignal(object)  # Emits model item
    
    def __init__(self, main_window, scene_controller, canvas_controller):
        """
        Initialize the equipment controller.
        
        Args:
            main_window: Main application window
            scene_controller: Scene controller instance
            canvas_controller: Canvas controller instance
        """
        super().__init__(main_window)
        
        self.main_window = main_window
        self.scene_controller = scene_controller
        self.canvas_controller = canvas_controller
        
        # Create equipment library panel
        self.equipment_library = EquipmentLibraryPanel()
        
        # Create properties panel (eventually will replace the basic one)
        self.properties_panel = PropertiesPanel()
        
        # Set up connections
        self.setup_connections()
    
    def setup_connections(self):
        """Set up signal connections."""
        # Connect equipment library selection to add equipment
        self.equipment_library.equipment_selected.connect(self.on_equipment_selected)
        self.equipment_library.equipment_dropped.connect(self.on_equipment_dropped)
        
        # Connect properties panel to scene controller
        self.properties_panel.property_changed.connect(self.on_property_changed)
        
        # Connect scene controller to properties panel
        self.scene_controller.item_selected.connect(self.on_item_selected)
    
    def replace_panels_in_main_window(self):
        """Replace the default panels in the main window with our enhanced versions."""
        # Find the splitter that holds the tool palette and properties panel
        if hasattr(self.main_window, 'h_splitter'):
            h_splitter = self.main_window.h_splitter
            
            # Find the index of the tool palette and properties panel
            tool_palette_index = h_splitter.indexOf(self.main_window.tool_palette)
            properties_panel_index = h_splitter.indexOf(self.main_window.properties_panel)
            
            # Get the current size of the tool palette
            tool_palette_width = h_splitter.sizes()[tool_palette_index]
            
            # Replace the tool palette with a container that holds the tool palette 
            # and equipment library in a vertical splitter
            tool_container = QWidget()
            tool_layout = QVBoxLayout(tool_container)
            tool_layout.setContentsMargins(0, 0, 0, 0)
            
            # Create vertical splitter for tool palette and equipment library
            v_splitter = QSplitter(Qt.Orientation.Vertical)
            v_splitter.addWidget(self.main_window.tool_palette)
            v_splitter.addWidget(self.equipment_library)
            
            # Set sizes with tool palette taking 40% and equipment library 60%
            v_splitter.setSizes([400, 600])
            
            tool_layout.addWidget(v_splitter)
            
            # Replace tool palette with the container, only if index exists
            if tool_palette_index >= 0:
                h_splitter.replaceWidget(tool_palette_index, tool_container)
            else:
                h_splitter.addWidget(tool_container)
            
            # Replace properties panel with our enhanced version
            h_splitter.replaceWidget(properties_panel_index, self.properties_panel)
            
            # Restore the width of the tool palette
            sizes = h_splitter.sizes()
            sizes[tool_palette_index] = tool_palette_width
            h_splitter.setSizes(sizes)
            
            # Store references to new panels
            self.main_window.equipment_library = self.equipment_library
            self.main_window.properties_panel = self.properties_panel
    
    def on_equipment_selected(self, equipment_id, equipment_data):
        """
        Handle equipment selection from the library.
        
        Args:
            equipment_id: ID of the selected equipment
            equipment_data: Data dictionary for the equipment
        """
        print(f"Selected equipment: {equipment_id} - {equipment_data['name']}")
    
    def on_equipment_dropped(self, equipment_id, equipment_data, position):
        """
        Handle equipment being dropped onto the canvas.
        
        Args:
            equipment_id: ID of the dropped equipment
            equipment_data: Data dictionary for the equipment
            position: Global position where equipment was dropped
        """
        # Convert global position to scene coordinates
        if hasattr(self.main_window, 'canvas_area') and self.main_window.canvas_area:
            canvas_view = self.main_window.canvas_area.view
            canvas_pos = canvas_view.mapFromGlobal(position)
            scene_pos = canvas_view.mapToScene(canvas_pos)
            
            # Forward to canvas controller
            if self.canvas_controller:
                self.canvas_controller.handle_equipment_drop(equipment_id, scene_pos)
    
    def on_property_changed(self, property_name, value):
        """
        Handle property changes from the properties panel.
        
        Args:
            property_name: Name of the property that changed
            value: New value for the property
        """
        # Get the currently selected item
        if hasattr(self.properties_panel, 'current_item') and self.properties_panel.current_item:
            # Update the model item
            if hasattr(self.properties_panel.current_item, property_name):
                setattr(self.properties_panel.current_item, property_name, value)
                
                # Update the scene
                self.scene_controller.item_modified.emit(self.properties_panel.current_item)
    
    def on_item_selected(self, model_item):
        """
        Handle item selection in the scene.
        
        Args:
            model_item: Selected model item or None if no selection
        """
        # Update the properties panel
        self.properties_panel.update_properties(model_item)


def setup_equipment_integration(main_window, scene_controller, canvas_controller):
    """
    Set up the equipment library and properties panel integration.
    
    Args:
        main_window: Main application window
        scene_controller: Scene controller instance
        canvas_controller: Canvas controller instance
    
    Returns:
        EquipmentController: The created equipment controller
    """
    # Create equipment controller
    equipment_controller = EquipmentController(main_window, scene_controller, canvas_controller)
    
    # Replace panels in main window
    equipment_controller.replace_panels_in_main_window()
    
    # Connect the properties panel with the canvas controller
    if hasattr(canvas_controller, 'connect_property_panel'):
        canvas_controller.connect_property_panel(equipment_controller.properties_panel)
    
    # Store reference to equipment controller
    main_window.equipment_controller = equipment_controller
    
    return equipment_controller
