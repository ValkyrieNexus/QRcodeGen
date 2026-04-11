"""QR Code Creator command definition, UI inputs, and event handlers."""

import adsk.core
import adsk.fusion
import traceback
import os

import config
from commands.generateQR import qr_logic
from commands.generateQR import fusion_geometry
from commands.generateQR import icons

# Module-level state
_handlers = []
_selected_svg_path = ''


def start():
    """Register the command in the Fusion UI."""
    app = adsk.core.Application.get()
    ui = app.userInterface

    cmd_def = ui.commandDefinitions.itemById(config.CMD_ID)
    if cmd_def:
        cmd_def.deleteMe()

    resource_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources')

    cmd_def = ui.commandDefinitions.addButtonDefinition(
        config.CMD_ID,
        config.CMD_NAME,
        config.CMD_DESCRIPTION,
        resource_folder if os.path.isdir(resource_folder) else ''
    )

    on_created = CommandCreatedHandler()
    cmd_def.commandCreated.add(on_created)
    _handlers.append(on_created)

    workspace = ui.workspaces.itemById(config.WORKSPACE_ID)
    if workspace:
        panel = workspace.toolbarPanels.itemById(config.PANEL_ID)
        if panel:
            existing = panel.controls.itemById(config.CMD_ID)
            if not existing:
                control = panel.controls.addCommand(cmd_def)
                control.isPromotedByDefault = True
                control.isPromoted = True


def stop():
    """Remove the command from the Fusion UI."""
    app = adsk.core.Application.get()
    ui = app.userInterface

    cmd_def = ui.commandDefinitions.itemById(config.CMD_ID)
    if cmd_def:
        cmd_def.deleteMe()

    workspace = ui.workspaces.itemById(config.WORKSPACE_ID)
    if workspace:
        panel = workspace.toolbarPanels.itemById(config.PANEL_ID)
        if panel:
            control = panel.controls.itemById(config.CMD_ID)
            if control:
                control.deleteMe()

    _handlers.clear()


def _find_input(inputs, input_id):
    """Find an input by ID, searching recursively inside groups."""
    inp = inputs.itemById(input_id)
    if inp:
        return inp
    for i in range(inputs.count):
        item = inputs.item(i)
        if hasattr(item, 'children'):
            found = _find_input(item.children, input_id)
            if found:
                return found
    return None


def _set_visible(inputs, input_id, visible):
    """Set visibility of an input by ID."""
    inp = _find_input(inputs, input_id)
    if inp:
        inp.isVisible = visible


# ──────────────────────────────────────────────────────────────────
#  IDs for each creation mode's fields, used for visibility toggling
# ──────────────────────────────────────────────────────────────────
_SIMPLE_IDS = ['text_to_encode']
_WEBSITE_IDS = ['website_url']
_VCARD_IDS = [
    'vc_first_name', 'vc_last_name', 'vc_phone', 'vc_mobile', 'vc_fax',
    'vc_email', 'vc_company', 'vc_job', 'vc_street', 'vc_city',
    'vc_zip', 'vc_state', 'vc_country', 'vc_website',
]
_WIFI_IDS = ['wifi_ssid', 'wifi_password', 'wifi_encryption']
_SEQ_IDS = ['seq_template', 'seq_start', 'seq_end', 'seq_leading_zeros']

_MODE_FIELDS = {
    config.MODE_SIMPLE: _SIMPLE_IDS,
    config.MODE_WEBSITE: _WEBSITE_IDS,
    config.MODE_VCARD: _VCARD_IDS,
    config.MODE_WIFI: _WIFI_IDS,
    config.MODE_SEQUENCE: _SEQ_IDS,
}
_ALL_MODE_IDS = _SIMPLE_IDS + _WEBSITE_IDS + _VCARD_IDS + _WIFI_IDS + _SEQ_IDS


class CommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def notify(self, args):
        try:
            cmd = args.command
            inputs = cmd.commandInputs

            # ── Creation Mode ──
            mode_input = inputs.addDropDownCommandInput(
                'creation_mode', 'Creation Mode',
                adsk.core.DropDownStyles.TextListDropDownStyle
            )
            for mode in config.CREATION_MODES:
                mode_input.listItems.add(mode, mode == config.MODE_SIMPLE)

            # ── Settings: Simple (visible by default) ──
            inputs.addTextBoxCommandInput('text_to_encode', 'Text to Encode', '', 3, False)

            # ── Settings: Website/URL ──
            _add_hidden(inputs.addStringValueInput('website_url', 'URL', 'https://'))

            # ── Settings: vCard ──
            for fid, label in [
                ('vc_first_name', 'First Name'), ('vc_last_name', 'Last Name'),
                ('vc_phone', 'Phone'), ('vc_mobile', 'Mobile'),
                ('vc_fax', 'Fax'), ('vc_email', 'Email'),
                ('vc_company', 'Company'), ('vc_job', 'Job'),
                ('vc_street', 'Street'), ('vc_city', 'City'),
                ('vc_zip', 'ZIP Code'), ('vc_state', 'State'),
                ('vc_country', 'Country'), ('vc_website', 'Website'),
            ]:
                _add_hidden(inputs.addStringValueInput(fid, label, ''))

            # ── Settings: WiFi ──
            _add_hidden(inputs.addStringValueInput('wifi_ssid', 'SSID', ''))
            _add_hidden(inputs.addStringValueInput('wifi_password', 'Password', ''))
            wifi_enc = inputs.addDropDownCommandInput(
                'wifi_encryption', 'Encryption',
                adsk.core.DropDownStyles.TextListDropDownStyle
            )
            wifi_enc.listItems.add('WPA', True)
            wifi_enc.listItems.add('WEP', False)
            wifi_enc.listItems.add('None', False)
            _add_hidden(wifi_enc)

            # ── Settings: Sequence ──
            _add_hidden(inputs.addStringValueInput('seq_template', 'Sequence to Encode', 'Part /#/'))
            _add_hidden(inputs.addIntegerSpinnerCommandInput('seq_start', 'Sequence Start', 1, 9999, 1, 1))
            _add_hidden(inputs.addIntegerSpinnerCommandInput('seq_end', 'Sequence End', 1, 9999, 1, 6))
            _add_hidden(inputs.addIntegerSpinnerCommandInput('seq_leading_zeros', 'Leading Zeros', 0, 10, 1, 2))

            # ── Placement Mode ──
            placement_group = inputs.addGroupCommandInput('placement_group', 'Placement')
            placement_group.isExpanded = True
            pg = placement_group.children

            place_dd = pg.addDropDownCommandInput(
                'placement_mode', 'Mode', adsk.core.DropDownStyles.TextListDropDownStyle)
            place_dd.listItems.add(config.PLACEMENT_STANDALONE, True)
            place_dd.listItems.add(config.PLACEMENT_ON_FACE, False)

            # Face selection (only visible in Place on Face mode)
            face_sel = pg.addSelectionInput('target_face', 'Target Face',
                                            'Select a planar face to place QR on')
            face_sel.addSelectionFilter('PlanarFaces')
            face_sel.setSelectionLimits(0, 1)
            _add_hidden(face_sel)

            # ── Style Options (group) ──
            style_group = inputs.addGroupCommandInput('style_group', 'Style Options')
            style_group.isExpanded = True
            sc = style_group.children

            style_dd = sc.addDropDownCommandInput(
                'style', 'Style', adsk.core.DropDownStyles.TextListDropDownStyle)
            style_dd.listItems.add(config.STYLE_SQUARE, True)
            style_dd.listItems.add(config.STYLE_CIRCLE, False)

            sc.addValueInput('segment_size', 'Segment Size', 'mm',
                             adsk.core.ValueInput.createByReal(fusion_geometry.mm_to_cm(config.DEFAULT_SEGMENT_SIZE_MM)))
            sc.addValueInput('segment_spacing', 'Segment Spacing', 'mm',
                             adsk.core.ValueInput.createByReal(fusion_geometry.mm_to_cm(config.DEFAULT_SEGMENT_SPACING_MM)))

            sc.addBoolValueInput('frame_enabled', 'Frame', True, '', False)
            _add_hidden(sc.addValueInput('frame_size', 'Frame Size', 'mm',
                                         adsk.core.ValueInput.createByReal(fusion_geometry.mm_to_cm(config.DEFAULT_FRAME_SIZE_MM))))

            sc.addValueInput('extrude_distance', 'Depth / Height', 'mm',
                             adsk.core.ValueInput.createByReal(fusion_geometry.mm_to_cm(config.DEFAULT_EXTRUDE_DISTANCE_MM)))

            icon_dd = sc.addDropDownCommandInput(
                'icon_select', 'Icon', adsk.core.DropDownStyles.TextListDropDownStyle)
            for name in icons.ICON_NAMES:
                icon_dd.listItems.add(name, name == 'No Icon')

            _add_hidden(sc.addTextBoxCommandInput(
                'svg_path_display', 'Logo File', '<i>No file selected</i>', 1, True))

            ec_dd = sc.addDropDownCommandInput(
                'error_correction', 'Error Correction', adsk.core.DropDownStyles.TextListDropDownStyle)
            for level in config.EC_LEVELS:
                ec_dd.listItems.add(level, level == 'H (30%)')

            sc.addBoolValueInput('qr_title', 'QR Title', True, '', False)

            # ── Info (read-only) ──
            info_group = inputs.addGroupCommandInput('info_group', 'Info')
            info_group.isExpanded = True
            ic = info_group.children
            ic.addTextBoxCommandInput('finish_size', 'Finish Size', '-- x --', 1, True)
            ic.addTextBoxCommandInput('segments', 'Segments', '--', 1, True)

            # Connect handlers
            on_changed = InputChangedHandler()
            cmd.inputChanged.add(on_changed)
            _handlers.append(on_changed)

            on_validate = ValidateInputsHandler()
            cmd.validateInputs.add(on_validate)
            _handlers.append(on_validate)

            on_execute = ExecuteHandler()
            cmd.execute.add(on_execute)
            _handlers.append(on_execute)

        except Exception:
            app = adsk.core.Application.get()
            app.userInterface.messageBox(traceback.format_exc())


def _add_hidden(inp):
    """Helper: set an input to hidden immediately after creation."""
    inp.isVisible = False
    return inp


def _get_mode(inputs):
    mode_input = _find_input(inputs, 'creation_mode')
    if mode_input and mode_input.selectedItem:
        return mode_input.selectedItem.name
    return config.MODE_SIMPLE


def _update_visibility(inputs):
    """Show/hide fields based on creation mode and toggles."""
    mode = _get_mode(inputs)

    # Show only fields for the active mode, hide all others
    active_ids = _MODE_FIELDS.get(mode, [])
    for fid in _ALL_MODE_IDS:
        _set_visible(inputs, fid, fid in active_ids)

    # Placement mode: show face selection only in Place on Face mode
    place_inp = _find_input(inputs, 'placement_mode')
    is_on_face = place_inp and place_inp.selectedItem and place_inp.selectedItem.name == config.PLACEMENT_ON_FACE
    _set_visible(inputs, 'target_face', is_on_face)

    # Frame size: visible only when Frame is checked
    frame_inp = _find_input(inputs, 'frame_enabled')
    if frame_inp:
        _set_visible(inputs, 'frame_size', frame_inp.value)

    # SVG path display: visible only when Custom SVG is selected
    icon_inp = _find_input(inputs, 'icon_select')
    if icon_inp and icon_inp.selectedItem:
        is_svg = icon_inp.selectedItem.name == 'Custom SVG...'
        _set_visible(inputs, 'svg_path_display', is_svg)

        # Force error correction to H when any icon is selected
        if icon_inp.selectedItem.name != 'No Icon':
            ec = _find_input(inputs, 'error_correction')
            if ec:
                for i in range(ec.listItems.count):
                    item = ec.listItems.item(i)
                    item.isSelected = (item.name == 'H (30%)')


def _get_qr_data(inputs):
    """Build the QR data string from current inputs."""
    mode = _get_mode(inputs)

    if mode == config.MODE_SIMPLE:
        inp = _find_input(inputs, 'text_to_encode')
        return inp.text if inp else ''

    elif mode == config.MODE_WEBSITE:
        inp = _find_input(inputs, 'website_url')
        return inp.value if inp else ''

    elif mode == config.MODE_VCARD:
        fields = {}
        field_map = {
            'vc_first_name': 'first_name', 'vc_last_name': 'last_name',
            'vc_phone': 'phone', 'vc_mobile': 'mobile',
            'vc_email': 'email', 'vc_company': 'company', 'vc_job': 'job',
            'vc_street': 'street', 'vc_city': 'city', 'vc_zip': 'zip',
            'vc_state': 'state', 'vc_country': 'country', 'vc_website': 'website',
        }
        for input_id, field_name in field_map.items():
            inp = _find_input(inputs, input_id)
            if inp:
                fields[field_name] = inp.value
        return qr_logic.encode_vcard(fields)

    elif mode == config.MODE_WIFI:
        ssid_inp = _find_input(inputs, 'wifi_ssid')
        pass_inp = _find_input(inputs, 'wifi_password')
        enc_inp = _find_input(inputs, 'wifi_encryption')
        ssid = ssid_inp.value if ssid_inp else ''
        password = pass_inp.value if pass_inp else ''
        enc = 'WPA'
        if enc_inp and enc_inp.selectedItem:
            enc_name = enc_inp.selectedItem.name
            enc = 'nopass' if enc_name == 'None' else enc_name
        return qr_logic.encode_wifi(ssid, password, enc)

    elif mode == config.MODE_SEQUENCE:
        tmpl = _find_input(inputs, 'seq_template')
        start = _find_input(inputs, 'seq_start')
        lz = _find_input(inputs, 'seq_leading_zeros')
        template = tmpl.value if tmpl else 'Part /#/'
        s = start.value if start else 1
        z = lz.value if lz else 0
        items = qr_logic.generate_sequence_data(template, s, s, z)
        return items[0] if items else template

    return ''


def _update_info(inputs):
    """Update the read-only info fields."""
    finish_size = _find_input(inputs, 'finish_size')
    segments = _find_input(inputs, 'segments')
    if not finish_size or not segments:
        return
    try:
        data = _get_qr_data(inputs)
        if not data:
            finish_size.text = '-- x --'
            segments.text = '--'
            return

        ec = _find_input(inputs, 'error_correction')
        ec_str = 'H'
        if ec and ec.selectedItem:
            ec_str = config.EC_MAP.get(ec.selectedItem.name, 'H')

        result = qr_logic.estimate_qr_version(data, ec_str)
        if result[0] is None:
            finish_size.text = 'Data too long'
            segments.text = '--'
            return

        version, module_count = result
        border = 4
        seg_inp = _find_input(inputs, 'segment_size')
        seg_mm = seg_inp.value * 10.0 if seg_inp else config.DEFAULT_SEGMENT_SIZE_MM

        total_modules = module_count + 2 * border
        total_mm = total_modules * seg_mm

        frame_inp = _find_input(inputs, 'frame_enabled')
        frame_size_inp = _find_input(inputs, 'frame_size')
        if frame_inp and frame_inp.value and frame_size_inp:
            total_mm += 2 * frame_size_inp.value * 10.0

        mode = _get_mode(inputs)
        qr_count = 1
        if mode == config.MODE_SEQUENCE:
            s = _find_input(inputs, 'seq_start')
            e = _find_input(inputs, 'seq_end')
            if s and e:
                qr_count = max(1, e.value - s.value + 1)

        size_str = f'{total_mm:.1f}mm x {total_mm:.1f}mm'
        if qr_count > 1:
            size_str += f' (x{qr_count})'
        finish_size.text = size_str

        matrix = qr_logic.generate_matrix(data, ec_str, border)
        segments.text = str(sum(1 for row in matrix for v in row if v))

    except Exception:
        finish_size.text = '--'
        segments.text = '--'


class InputChangedHandler(adsk.core.InputChangedEventHandler):
    def notify(self, args):
        try:
            inputs = args.inputs
            changed_id = args.input.id

            if changed_id == 'icon_select':
                icon_inp = _find_input(inputs, 'icon_select')
                if icon_inp and icon_inp.selectedItem and icon_inp.selectedItem.name == 'Custom SVG...':
                    global _selected_svg_path
                    app = adsk.core.Application.get()
                    dlg = app.userInterface.createFileDialog()
                    dlg.title = 'Select SVG Logo'
                    dlg.filter = 'SVG files (*.svg);;All files (*.*)'
                    if dlg.showOpen() == adsk.core.DialogResults.DialogOK:
                        _selected_svg_path = dlg.filename
                        disp = _find_input(inputs, 'svg_path_display')
                        if disp:
                            disp.text = os.path.basename(_selected_svg_path)
                    else:
                        _selected_svg_path = ''
                        for i in range(icon_inp.listItems.count):
                            if icon_inp.listItems.item(i).name == 'No Icon':
                                icon_inp.listItems.item(i).isSelected = True
                                break
                        disp = _find_input(inputs, 'svg_path_display')
                        if disp:
                            disp.text = '<i>No file selected</i>'

            _update_visibility(inputs)
            _update_info(inputs)
        except Exception:
            pass


class ValidateInputsHandler(adsk.core.ValidateInputsEventHandler):
    def notify(self, args):
        try:
            inputs = args.inputs
            mode = _get_mode(inputs)

            if mode == config.MODE_SIMPLE:
                inp = _find_input(inputs, 'text_to_encode')
                if not inp or not inp.text.strip():
                    args.areInputsValid = False
                    return

            elif mode == config.MODE_WEBSITE:
                inp = _find_input(inputs, 'website_url')
                if not inp or not inp.value.strip() or inp.value.strip() == 'https://':
                    args.areInputsValid = False
                    return

            elif mode == config.MODE_VCARD:
                fn = _find_input(inputs, 'vc_first_name')
                ln = _find_input(inputs, 'vc_last_name')
                if (not fn or not fn.value.strip()) and (not ln or not ln.value.strip()):
                    args.areInputsValid = False
                    return

            elif mode == config.MODE_WIFI:
                ssid = _find_input(inputs, 'wifi_ssid')
                if not ssid or not ssid.value.strip():
                    args.areInputsValid = False
                    return

            elif mode == config.MODE_SEQUENCE:
                tmpl = _find_input(inputs, 'seq_template')
                if not tmpl or '/#/' not in tmpl.value:
                    args.areInputsValid = False
                    return
                s = _find_input(inputs, 'seq_start')
                e = _find_input(inputs, 'seq_end')
                if s and e and e.value < s.value:
                    args.areInputsValid = False
                    return

            seg = _find_input(inputs, 'segment_size')
            if seg and seg.value <= 0:
                args.areInputsValid = False
                return

            ext_d = _find_input(inputs, 'extrude_distance')
            if ext_d and ext_d.value <= 0:
                args.areInputsValid = False
                return

            # Place on Face requires a face selection
            place_inp = _find_input(inputs, 'placement_mode')
            if place_inp and place_inp.selectedItem and place_inp.selectedItem.name == config.PLACEMENT_ON_FACE:
                face_sel = _find_input(inputs, 'target_face')
                if not face_sel or face_sel.selectionCount == 0:
                    args.areInputsValid = False
                    return

            icon_inp = _find_input(inputs, 'icon_select')
            if icon_inp and icon_inp.selectedItem:
                if icon_inp.selectedItem.name == 'Custom SVG...' and not _selected_svg_path:
                    args.areInputsValid = False
                    return

            args.areInputsValid = True
        except Exception:
            args.areInputsValid = False


class ExecuteHandler(adsk.core.CommandEventHandler):
    def notify(self, args):
        try:
            app = adsk.core.Application.get()
            ui = app.userInterface
            design = adsk.fusion.Design.cast(app.activeProduct)
            if not design:
                ui.messageBox('Please open or create a Design document first.')
                return

            inputs = args.command.commandInputs
            root_comp = design.rootComponent

            # Gather inputs
            mode = _get_mode(inputs)

            style_inp = _find_input(inputs, 'style')
            style = style_inp.selectedItem.name if style_inp and style_inp.selectedItem else config.STYLE_SQUARE

            seg_size_cm = _find_input(inputs, 'segment_size').value
            spacing_cm = _find_input(inputs, 'segment_spacing').value

            frame_inp = _find_input(inputs, 'frame_enabled')
            frame_on = frame_inp.value if frame_inp else False
            frame_size_cm = _find_input(inputs, 'frame_size').value if frame_on else 0

            extrude_cm = _find_input(inputs, 'extrude_distance').value

            # Placement mode
            place_inp = _find_input(inputs, 'placement_mode')
            placement = place_inp.selectedItem.name if place_inp and place_inp.selectedItem else config.PLACEMENT_STANDALONE
            target_face = None
            target_body = None
            if placement == config.PLACEMENT_ON_FACE:
                face_sel = _find_input(inputs, 'target_face')
                if face_sel and face_sel.selectionCount > 0:
                    target_face = face_sel.selection(0).entity
                    target_body = target_face.body

            ec_inp = _find_input(inputs, 'error_correction')
            ec_str = 'H'
            if ec_inp and ec_inp.selectedItem:
                ec_str = config.EC_MAP.get(ec_inp.selectedItem.name, 'H')

            icon_inp = _find_input(inputs, 'icon_select')
            icon_name = icon_inp.selectedItem.name if icon_inp and icon_inp.selectedItem else 'No Icon'

            if icon_name != 'No Icon':
                ec_str = 'H'

            # Build data list
            data_list = []
            if mode == config.MODE_SEQUENCE:
                tmpl = _find_input(inputs, 'seq_template').value
                start = _find_input(inputs, 'seq_start').value
                end = _find_input(inputs, 'seq_end').value
                lz = _find_input(inputs, 'seq_leading_zeros').value
                data_list = qr_logic.generate_sequence_data(tmpl, start, end, lz)
            else:
                data_list = [_get_qr_data(inputs)]

            if not data_list:
                ui.messageBox('No data to encode.')
                return

            # Progress dialog
            pd = ui.createProgressDialog()
            pd.cancelButtonText = 'Cancel'
            pd.isCancelButtonShown = True
            pd.show('QR Code Creator', f'Generating {len(data_list)} QR code(s)...', 0, len(data_list) * 100)

            # Use minimal border (1 module) -- the frame serves as the quiet zone
            border = 1 if frame_on else 4

            for idx, data in enumerate(data_list):
                if pd.wasCancelled:
                    break

                pd.message = f'Generating QR code {idx + 1} of {len(data_list)}...'

                try:
                    matrix = qr_logic.generate_matrix(data, ec_str, border)
                except Exception as e:
                    ui.messageBox(f'Failed to generate QR code:\n{str(e)}')
                    continue

                total_rows = len(matrix)
                total_size_cm = total_rows * seg_size_cm

                # Clear center for icon
                icon_zone = None
                if icon_name != 'No Icon':
                    zone_modules = qr_logic.compute_icon_zone_modules(matrix, 20)
                    icon_zone = qr_logic.clear_center_zone(matrix, zone_modules)

                module_positions = qr_logic.compute_rectangles(matrix, dark=True)

                # ── Build icon callback if needed ──
                icon_sketch_fn = None
                if icon_name != 'No Icon' and icon_zone:
                    center_cm = total_size_cm / 2.0
                    zone_cm = (icon_zone[2] - icon_zone[0]) * seg_size_cm

                    if icon_name == 'Custom SVG...' and _selected_svg_path:
                        svg_path = _selected_svg_path
                        def icon_sketch_fn(sketch, _ctr=center_cm, _zone=zone_cm, _path=svg_path):
                            # Two-pass SVG: measure then import centered
                            temp = sketch.parentComponent.sketches.add(sketch.referencePlane)
                            temp.importSVG(_path, 0, 0, 1.0)
                            bb = temp.boundingBox
                            sw = bb.maxPoint.x - bb.minPoint.x
                            sh = bb.maxPoint.y - bb.minPoint.y
                            sm = max(sw, sh)
                            temp.deleteMe()
                            if sm > 0:
                                sc = _zone / sm
                                xo = _ctr - sw * sc / 2.0 - bb.minPoint.x * sc
                                yo = _ctr - sh * sc / 2.0 - bb.minPoint.y * sc
                                sketch.importSVG(_path, xo, yo, sc)
                    else:
                        def icon_sketch_fn(sketch, _name=icon_name, _ctr=center_cm, _zone=zone_cm):
                            icons.draw_icon(sketch, _name, _ctr, _ctr, _zone)

                # ════════════════════════════════════════════
                #  PLACE ON FACE: cut recess + fill on target
                # ════════════════════════════════════════════
                if placement == config.PLACEMENT_ON_FACE and target_face and target_body:
                    target_comp = target_body.parentComponent
                    pd.message = f'Placing QR code on face...'

                    fusion_geometry.cut_and_fill_on_face(
                        target_comp, target_face, target_body,
                        module_positions, total_rows, total_size_cm,
                        seg_size_cm, spacing_cm, extrude_cm, style,
                        frame_on, frame_size_cm, icon_sketch_fn
                    )

                # ════════════════════════════════════════════
                #  STANDALONE: create component with bodies
                # ════════════════════════════════════════════
                else:
                    comp_name = data[:40] if mode != config.MODE_SEQUENCE else data
                    comp = fusion_geometry.create_component(root_comp, comp_name)

                    # Sequence grid layout
                    if mode == config.MODE_SEQUENCE and idx > 0:
                        cols = 3
                        gap_cm = fusion_geometry.mm_to_cm(20)
                        total_with_frame = total_size_cm + 2 * frame_size_cm
                        ox = (idx % cols) * (total_with_frame + gap_cm)
                        oy = -(idx // cols) * (total_with_frame + gap_cm)
                        occ = root_comp.occurrences.item(root_comp.occurrences.count - 1)
                        t = occ.transform
                        t.translation = adsk.core.Vector3D.create(ox, oy, 0)
                        occ.transform = t

                    pd.progressValue = idx * 100 + 5

                    # Base plate
                    bp_sketch = comp.sketches.add(comp.xYConstructionPlane)
                    bp_sketch.name = 'QR_BasePlate_Sketch'
                    if frame_on:
                        bp_p1 = adsk.core.Point3D.create(-frame_size_cm, -frame_size_cm, 0)
                        bp_p2 = adsk.core.Point3D.create(
                            total_size_cm + frame_size_cm,
                            total_size_cm + frame_size_cm, 0)
                    else:
                        bp_p1 = adsk.core.Point3D.create(0, 0, 0)
                        bp_p2 = adsk.core.Point3D.create(total_size_cm, total_size_cm, 0)
                    bp_sketch.sketchCurves.sketchLines.addTwoPointRectangle(bp_p1, bp_p2)
                    base_depth_cm = extrude_cm * 0.5
                    bp_prof = bp_sketch.profiles.item(0)
                    bp_ext = comp.features.extrudeFeatures.createInput(
                        bp_prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
                    bp_ext.setDistanceExtent(False, adsk.core.ValueInput.createByReal(base_depth_cm))
                    bp_feat = comp.features.extrudeFeatures.add(bp_ext)
                    if bp_feat and bp_feat.bodies.count > 0:
                        bp_feat.bodies.item(0).name = 'QR_BasePlate'

                    pd.progressValue = idx * 100 + 10

                    # Frame
                    if frame_on:
                        fs = comp.sketches.add(comp.xYConstructionPlane)
                        fs.name = 'QR_Frame_Sketch'
                        fusion_geometry.draw_frame(fs, total_size_cm, frame_size_cm)
                        fusion_geometry.extrude_frame_profile(comp, fs, extrude_cm)

                    pd.progressValue = idx * 100 + 20

                    # Modules
                    ms = comp.sketches.add(comp.xYConstructionPlane)
                    ms.name = 'QR_Modules_Sketch'
                    fusion_geometry.draw_all_modules(ms, module_positions, total_rows, seg_size_cm, spacing_cm, style)

                    pd.progressValue = idx * 100 + 50

                    pd.message = f'Extruding QR code {idx + 1}...'
                    fusion_geometry.extrude_profiles_combined(comp, ms, extrude_cm, 'QR_Modules', False)

                    pd.progressValue = idx * 100 + 80

                    # Icon
                    if icon_sketch_fn:
                        isk = comp.sketches.add(comp.xYConstructionPlane)
                        isk.name = 'QR_Icon_Sketch'
                        icon_sketch_fn(isk)
                        fusion_geometry.extrude_profiles_combined(comp, isk, extrude_cm, 'QR_Icon', True)

                pd.progressValue = idx * 100 + 100

            pd.hide()

        except Exception:
            app = adsk.core.Application.get()
            app.userInterface.messageBox(f'QR Code generation failed:\n{traceback.format_exc()}')
