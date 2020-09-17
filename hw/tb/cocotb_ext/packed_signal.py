# TODO(ttrippel): add license
import math

import prettytable
from cocotb.binary import BinaryValue


class Signal:
  def __init__(self, name: str, width: int, offset: int):
    self.name = name
    self.width = width
    self.offset = offset


class PackedSignal():
  # TODO(ttrippel): clean this up
  def __init__(self, parent_sig, child_sigs, log):
    self._parent_sig = parent_sig
    self._child_sigs = {}
    self._log = log

    # unpack children
    csig_offset = 0
    for csig_name, csig_width in child_sigs.items():
      self._child_sigs[csig_name] = Signal(csig_name, csig_width, csig_offset)
      csig_offset += csig_width
    self._width = csig_offset
    assert self._width == len(self._parent_sig.value.binstr), \
        "{self.parent_sig._name} signal width settings are incorrect."

  def _get_child_binstr(self, csig: Signal) -> str:
    return self._parent_sig.value.binstr[csig.offset:csig.offset + csig.width]

  def _get_child_int(self, csig):
    return int(self._get_child_binstr(csig), 2)

  def pack(self, **kwargs) -> BinaryValue:
    binstr = "0" * self._width
    for csig_name, csig_value in kwargs.items():
      self._log.debug(f"Packing {csig_name} into {self._parent_sig._name} ...")
      # TODO(ttrippel): check if child signal name exists
      csig = self._child_sigs[csig_name]
      # TODO(ttrippel): check that value is valid for width
      binstr = binstr[:csig.offset] + f"{csig_value:0{csig.width}b}" + binstr[
          csig.offset + csig.width:]
    return BinaryValue(binstr)

  def unpack(self, csig_name: str) -> BinaryValue:
    # TODO(ttrippel): check if child signal name exists
    self._log.debug(f"Unpacking {csig_name} from {self._parent_sig._name} ...")
    csig = self._child_sigs[csig_name]
    return BinaryValue(self._get_child_binstr(csig))

  def signal2str(self) -> str:
    tl_table = prettytable.PrettyTable(header=True)
    tl_table.field_names = ["Signal", "Width", "Hex Value", "Binary Value"]
    for csig_name, csig in self._child_sigs.items():
      # get binary and int representations of child signal
      csig_binstr = self._get_child_binstr(csig)
      csig_int = self._get_child_int(csig)
      csig_hex_width = math.ceil(csig.width / 4.0)
      tl_table.add_row([
          csig_name, csig.width, f"{csig_int:0>{csig_hex_width}X}", csig_binstr
      ])
    tl_table.align = "l"
    tl_table.title = f"{self._parent_sig._name} ({self._width} bits)"
    return str(tl_table)
