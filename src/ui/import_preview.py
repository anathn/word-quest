"""
Import Preview Component

Provides UI for previewing and selecting words to import from CSV.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Optional, Callable, Dict
from src.words.csv_importer import ParsedWord, Difficulty


class ImportPreview(tk.Toplevel):
    """
    Dialog for previewing and selecting CSV import rows.
    
    Features:
    - Scrollable table showing all parsed words
    - Checkboxes for selective import
    - Visual indicators for errors
    - Import statistics
    """
    
    def __init__(
        self,
        parent: tk.Misc,
        parsed_words: List[ParsedWord],
        on_import: Callable[[List[ParsedWord]], None],
        on_cancel: Optional[Callable[[], None]] = None
    ):
        """
        Initialize import preview dialog.
        
        Args:
            parent: Parent widget
            parsed_words: List of ParsedWord objects to preview
            on_import: Callback with selected words when import confirmed
            on_cancel: Optional callback when cancelled
        """
        super().__init__(parent)
        
        self.parsed_words = parsed_words
        self.on_import = on_import
        self.on_cancel = on_cancel
        self.selected_indices: set = set()
        
        self.title("Import Preview")
        self.geometry("800x600")
        self.minsize(600, 400)
        
        # Track which rows are selected (default: all valid rows selected)
        for i, word in enumerate(parsed_words):
            if word.is_valid:
                self.selected_indices.add(i)
        
        self._setup_ui()
        self._populate_table()
        self._update_stats()
    
    def _setup_ui(self):
        """Set up the dialog UI components."""
        # Main frame with padding
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title and instructions
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(
            title_frame,
            text="Review Import - Select words to import",
            font=("Helvetica", 14, "bold")
        ).pack(side=tk.LEFT)
        
        # Stats display
        self.stats_label = ttk.Label(title_frame, text="", font=("Helvetica", 10))
        self.stats_label.pack(side=tk.RIGHT)
        
        # Table frame
        table_frame = ttk.Frame(main_frame)
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create treeview with scrollbar
        columns = ("select", "row", "word", "definition", "difficulty", "status")
        
        # Table headers
        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="none"
        )
        
        # Configure columns
        self.tree.heading("select", text="✓")
        self.tree.heading("row", text="Row")
        self.tree.heading("word", text="Word")
        self.tree.heading("definition", text="Definition")
        self.tree.heading("difficulty", text="Difficulty")
        self.tree.heading("status", text="Status")
        
        self.tree.column("select", width=40, minwidth=30)
        self.tree.column("row", width=50, minwidth=40)
        self.tree.column("word", width=120, minwidth=100)
        self.tree.column("definition", width=250, minwidth=200)
        self.tree.column("difficulty", width=80, minwidth=60)
        self.tree.column("status", width=120, minwidth=100)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind selection events
        self.tree.bind("<Button-1>", self._on_click)
        self.tree.bind("<Double-1>", self._on_double_click)
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Import all button
        self.import_btn = ttk.Button(
            button_frame,
            text="Import Selected",
            command=self._confirm_import,
            state=tk.NORMAL
        )
        self.import_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Select all button
        ttk.Button(
            button_frame,
            text="Select All",
            command=self._select_all
        ).pack(side=tk.RIGHT, padx=5)
        
        # Deselect all button
        ttk.Button(
            button_frame,
            text="Deselect All",
            command=self._deselect_all
        ).pack(side=tk.RIGHT, padx=5)
        
        # Cancel button
        ttk.Button(
            button_frame,
            text="Cancel",
            command=self._cancel
        ).pack(side=tk.RIGHT)
        
        # Configure tag colors for status
        self.tree.tag_configure("error", background="#ffe6e6")
        self.tree.tag_configure("warning", background="#fff2cc")
        self.tree.tag_configure("valid", background="")
    
    def _populate_table(self):
        """Populate the treeview with parsed words."""
        for i, word in enumerate(self.parsed_words):
            # Determine status text and tag
            if word.is_valid:
                status_text = "✓ Valid"
                tag = "valid"
            else:
                status_text = f"✗ {word.error}"
                tag = "error"
            
            # Difficulty display
            diff_display = word.difficulty.value.title() if word.difficulty else "Medium"
            
            # Definition truncated if too long
            definition = word.definition if len(word.definition) <= 40 else word.definition[:37] + "..."
            
            # Insert row
            self.tree.insert(
                "",
                tk.END,
                tags=(tag,),
                values=(
                    "",  # Select column (checkbox visual)
                    word.row_number,
                    word.spelling,
                    definition,
                    diff_display,
                    status_text
                )
            )
    
    def _on_click(self, event):
        """Handle click on treeview item."""
        region = self.tree.identify_region(event.x, event.y)
        
        if region == "cell":
            item = self.tree.identify_row(event.y)
            if item:
                # Get the select column (first column)
                col = self.tree["columns"][0]
                col_index = self.tree["columns"].index(col)
                
                cell_x, cell_y = event.x, event.y
                
                # Get cell bounds
                bbox = self.tree.bbox(item, col)
                if bbox:
                    cell_x, cell_y, cell_w, cell_h = bbox
                    
                    # Check if clicked in select column
                    if col_index == 0:
                        self._toggle_selection(item)
    
    def _on_double_click(self, event):
        """Handle double-click to toggle selection."""
        item = self.tree.identify_row(event.y)
        if item:
            self._toggle_selection(item)
    
    def _toggle_selection(self, item):
        """Toggle selection state for an item."""
        if item in self.selected_indices:
            self.selected_indices.remove(item)
            self.tree.item(item, values=self._get_row_values(item, False))
        else:
            self.selected_indices.add(item)
            self.tree.item(item, values=self._get_row_values(item, True))
        
        self._update_stats()
    
    def _get_row_values(self, item: str, selected: bool) -> tuple:
        """Get row values with updated select status."""
        values = list(self.tree.item(item, "values"))
        values[0] = "✓" if selected else ""  # Select column
        return tuple(values)
    
    def _select_all(self):
        """Select all valid rows."""
        for i, word in enumerate(self.parsed_words):
            if word.is_valid:
                item = self.tree.get_children()[i]
                if item not in self.selected_indices:
                    self.selected_indices.add(item)
                    self.tree.item(item, values=self._get_row_values(item, True))
        self._update_stats()
    
    def _deselect_all(self):
        """Deselect all rows."""
        for item in list(self.selected_indices):
            self.selected_indices.remove(item)
            self.tree.item(item, values=self._get_row_values(item, False))
        self._update_stats()
    
    def _update_stats(self):
        """Update statistics display."""
        total = len(self.parsed_words)
        valid = sum(1 for w in self.parsed_words if w.is_valid)
        selected = len(self.selected_indices)
        errors = total - valid
        
        self.stats_label.config(
            text=f"Total: {total} | Valid: {valid} | Errors: {errors} | Selected: {selected}"
        )
        
        # Disable import button if nothing selected
        if selected == 0:
            self.import_btn.config(state=tk.DISABLED)
        else:
            self.import_btn.config(state=tk.NORMAL)
    
    def _confirm_import(self):
        """Handle import confirmation."""
        # Get selected words
        selected_words = [
            self.parsed_words[i]
            for i in range(len(self.parsed_words))
            if i in self.selected_indices
        ]
        
        # Validate at least one word selected
        if not selected_words:
            messagebox.showwarning(
                "No Selection",
                "Please select at least one word to import."
            )
            return
        
        # Call import callback
        self.on_import(selected_words)
        self.destroy()
    
    def _cancel(self):
        """Handle cancel action."""
        if self.on_cancel:
            self.on_cancel()
        self.destroy()


def create_import_preview(
    parent: tk.Misc,
    parsed_words: List[ParsedWord],
    on_import: Callable[[List[ParsedWord]], None],
    on_cancel: Optional[Callable[[], None]] = None
) -> ImportPreview:
    """
    Factory function to create import preview dialog.
    
    Args:
        parent: Parent widget
        parsed_words: List of parsed words to preview
        on_import: Callback for confirmed import
        on_cancel: Optional cancel callback
        
    Returns:
        ImportPreview dialog instance
    """
    return ImportPreview(parent, parsed_words, on_import, on_cancel)