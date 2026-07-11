"""
CSV Import Dialog

Main dialog for CSV word list import with file picker and import flow.
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Optional, Callable, List, Dict, Any
import os
import tempfile

from src.words.csv_importer import CSVImporter, ParsedWord, ImportResult, Difficulty
from src.ui.import_preview import create_import_preview
from src.components.word_manager import get_word_manager, SpellingWord


class CSVImportDialog(tk.Toplevel):
    """
    Dialog for importing word lists from CSV files.
    
    Features:
    - File picker with CSV filter
    - Parse preview with error highlighting
    - Selective import
    - Duplicate handling options
    - Import summary
    
    Usage:
        dialog = CSVImportDialog(parent, on_import=handler)
    """
    
    # Supported file extensions
    FILE_TYPES = [
        ("CSV Files", "*.csv"),
        ("Text Files", "*.txt"),
        ("All Files", "*.*")
    ]
    
    def __init__(
        self,
        parent: tk.Misc,
        on_import: Callable[[List[SpellingWord]], None],
        on_close: Optional[Callable[[], None]] = None,
        word_manager: Optional[Any] = None
    ):
        """
        Initialize CSV import dialog.
        
        Args:
            parent: Parent widget
            on_import: Callback with imported SpellingWord list
            on_close: Optional close callback
            word_manager: WordManager instance (uses global if None)
        """
        super().__init__(parent)
        
        self.on_import = on_import
        self.on_close = on_close
        self.word_manager = word_manager or get_word_manager()
        
        self.filepath: Optional[str] = None
        self.parsed_words: List[ParsedWord] = []
        
        self.title("Import Word List from CSV")
        self.geometry("500x400")
        self.minsize(400, 300)
        self.resizable(True, True)
        
        # Center on parent
        self._center_window()
        
        self._setup_ui()
    
    def _center_window(self):
        """Center the dialog on its parent."""
        self.update_idletasks()
        
        parent_x = self.winfo_rootx()
        parent_y = self.winfo_rooty()
        parent_w = self.winfo_width()
        parent_h = self.winfo_height()
        
        # Center relative to parent
        x = parent_x + (parent_w - self.winfo_width()) // 2
        y = parent_y + (parent_h - self.winfo_height()) // 2
        
        self.geometry(f"+{x}+{y}")
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(
            main_frame,
            text="CSV Word Import",
            font=("Helvetica", 16, "bold")
        )
        title_label.pack(pady=(0, 10))
        
        # Description
        desc_label = ttk.Label(
            main_frame,
            text="Select a CSV file containing spelling words. "
                 "Format: word, definition, difficulty (optional)",
            font=("Helvetica", 10),
            wraplength=400
        )
        desc_label.pack(pady=(0, 20))
        
        # File selection frame
        file_frame = ttk.LabelFrame(main_frame, text="File Selection", padding="10")
        file_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.file_label = ttk.Label(file_frame, text="No file selected", width=40)
        self.file_label.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            file_frame,
            text="Browse...",
            command=self._select_file
        ).pack(side=tk.RIGHT)
        
        # Options frame
        options_frame = ttk.LabelFrame(main_frame, text="Import Options", padding="10")
        options_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Duplicate handling
        self.duplicate_var = tk.StringVar(value="skip")
        ttk.Radiobutton(
            options_frame,
            text="Skip duplicates",
            variable=self.duplicate_var,
            value="skip"
        ).pack(anchor=tk.W)
        
        ttk.Radiobutton(
            options_frame,
            text="Overwrite duplicates",
            variable=self.duplicate_var,
            value="overwrite"
        ).pack(anchor=tk.W)
        
        # Auto-assign difficulty
        self.auto_diff_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame,
            text="Auto-assign difficulty if not specified",
            variable=self.auto_diff_var
        ).pack(anchor=tk.W)
        
        # Action buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(
            button_frame,
            text="Download Sample CSV",
            command=self._download_sample
        ).pack(side=tk.LEFT)
        
        ttk.Button(
            button_frame,
            text="Import",
            command=self._parse_and_preview,
            state=tk.DISABLED
        ).pack(side=tk.RIGHT, padx=(10, 0))
        
        ttk.Button(
            button_frame,
            text="Cancel",
            command=self._cancel
        ).pack(side=tk.RIGHT)
        
        # Status label
        self.status_label = ttk.Label(main_frame, text="", font=("Helvetica", 9))
        self.status_label.pack(pady=(10, 0))
    
    def _select_file(self):
        """Open file picker and select CSV file."""
        filepath = filedialog.askopenfilename(
            title="Select CSV File",
            filetypes=self.FILE_TYPES,
            parent=self
        )
        
        if filepath:
            self.filepath = filepath
            filename = os.path.basename(filepath)
            self.file_label.config(text=f"Selected: {filename}")
            
            # Enable import button
            for widget in self.winfo_children():
                if isinstance(widget, ttk.LabelFrame):
                    for child in widget.winfo_children():
                        if isinstance(child, ttk.Frame):
                            for btn in child.winfo_children():
                                if isinstance(btn, ttk.Button) and "Import" in btn.cget("text"):
                                    btn.config(state=tk.NORMAL)
            
            self.status_label.config(text="File selected. Click 'Import' to preview.")
    
    def _parse_and_preview(self):
        """Parse the CSV file and show preview dialog."""
        if not self.filepath:
            messagebox.showwarning("No File", "Please select a CSV file first.")
            return
        
        try:
            # Parse the file
            self.status_label.config(text="Parsing file...")
            self.update()
            
            result = CSVImporter(self.filepath).parse_file()
            
            self.parsed_words = result.successful + [
                ParsedWord("", "", Difficulty.MEDIUM, row, error)
                for row, error in result.skipped
            ]
            
            # Check if any valid words found
            valid_words = [w for w in self.parsed_words if w.is_valid]
            
            if not valid_words:
                messagebox.showerror(
                    "Import Failed",
                    "No valid words found in the CSV file.\n\n"
                    f"Errors:\n{'\n'.join(f'Row {r}: {e}' for r, e in result.skipped[:5])}"
                )
                self.status_label.config(text="Import failed. Try a different file.")
                return
            
            # Show preview dialog
            def on_import(selected_words: List[ParsedWord]):
                self._perform_import(selected_words)
            
            preview = create_import_preview(
                self,
                self.parsed_words,
                on_import,
                on_cancel=lambda: self.status_label.config(text="Preview cancelled.")
            )
            
            # Wait for preview to close
            preview.wait_window()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to parse CSV: {str(e)}")
            self.status_label.config(text="Error parsing file.")
    
    def _perform_import(self, parsed_words: List[ParsedWord]):
        """
        Perform the actual import of parsed words.
        
        Args:
            parsed_words: List of ParsedWord to import
        """
        try:
            # Filter valid words
            valid_words = [w for w in parsed_words if w.is_valid]
            
            if not valid_words:
                messagebox.showwarning("No Words", "No valid words to import.")
                return
            
            # Check for duplicates
            existing_texts = {w.text.upper() for w in self.word_manager.all_words}
            duplicates = []
            import_list = []
            
            for word in valid_words:
                if word.spelling in existing_texts:
                    duplicates.append(word.spelling)
                    if self.duplicate_var.get() == "overwrite":
                        import_list.append(word)
                else:
                    import_list.append(word)
            
            # Report duplicates
            if duplicates and self.duplicate_var.get() == "skip":
                skip_count = len(duplicates)
                confirm = messagebox.askyesno(
                    "Duplicates Found",
                    f"{skip_count} word(s) already exist and will be skipped.\n"
                    f"Continue with import of {len(import_list)} new word(s)?"
                )
                if not confirm:
                    return
            
            # Create SpellingWord objects
            word_count = 0
            for word in import_list:
                # Generate unique ID using UUID
                word_id = CSVImporter._generate_word_id()
                
                # Calculate starter letters based on difficulty
                starter_letters = 3 if word.difficulty == Difficulty.BEGINNER else (
                    2 if word.difficulty == Difficulty.MEDIUM else 1
                )
                
                spelling_word = SpellingWord(
                    id=word_id,
                    text=word.spelling,
                    definition=word.definition,
                    context_sentence="",  # Not available in CSV
                    difficulty=self._difficulty_to_int(word.difficulty),
                    starter_letters=starter_letters
                )
                
                # Add to word manager
                self.word_manager.add_word(spelling_word)
                word_count += 1
            
            # Save word lists
            self.word_manager.save_word_lists()
            
            # Show success message
            success_msg = (
                f"Import successful!\n\n"
                f"Added: {word_count} word(s)"
            )
            
            if self.duplicate_var.get() == "skip" and duplicates:
                success_msg = f"{success_msg}Skipped: {len(duplicates)} duplicate(s)"
            
            messagebox.showinfo("Import Complete", success_msg)
            
            # Call import callback
            self.on_import(self.word_manager.all_words[-word_count:] if word_count > 0 else [])
            
            # Close dialog
            self._close()
            
        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to import words: {str(e)}")
            self.status_label.config(text="Import failed.")
    
    def _difficulty_to_int(self, difficulty: Difficulty) -> int:
        """Convert Difficulty enum to int (1-3)."""
        return {
            Difficulty.BEGINNER: 1,
            Difficulty.MEDIUM: 2,
            Difficulty.ADVANCED: 3
        }.get(difficulty, 2)
    
    def _download_sample(self):
        """Download sample CSV template."""
        # Create temp directory if needed
        temp_dir = os.path.join(os.path.expanduser("~"), "word_quest_templates")
        os.makedirs(temp_dir, exist_ok=True)
        
        # Generate sample file path
        sample_path = os.path.join(temp_dir, "sample_word_list.csv")
        
        # Create sample CSV
        CSVImporter.create_sample_csv(sample_path)
        
        # Open file in default application
        try:
            if os.name == "nt":  # Windows
                os.startfile(sample_path)
            elif os.name == "posix":  # macOS/Linux
                import subprocess
                subprocess.run(["xdg-open" if os.name == "posix" else "open", sample_path])
            
            messagebox.showinfo(
                "Sample CSV",
                f"Sample CSV saved to:\n{sample_path}\n\n"
                "Open it to see the expected format."
            )
        except Exception as e:
            messagebox.showwarning(
                "Sample Not Opened",
                f"Sample CSV saved but could not be opened automatically:\n{sample_path}"
            )
    
    def _cancel(self):
        """Handle cancel action."""
        if self.on_close:
            self.on_close()
        self.destroy()
    
    def _close(self):
        """Close the dialog."""
        self.destroy()


def show_csv_import_dialog(
    parent: tk.Misc,
    on_import: Callable[[List[SpellingWord]], None],
    word_manager: Optional[Any] = None
) -> CSVImportDialog:
    """
    Factory function to show CSV import dialog.
    
    Args:
        parent: Parent widget
        on_import: Callback with imported words
        word_manager: Optional WordManager instance
        
    Returns:
        CSVImportDialog instance
    """
    return CSVImportDialog(parent, on_import, word_manager=word_manager)