#!/usr/bin/env python3

import time # to time calculations for users
import string # for easy retrieval of character ranges
from lxml import etree as et # for reading TEI XML inputs

"""
XML namespaces
"""
xml_ns = "http://www.w3.org/XML/1998/namespace"
tei_ns = "http://www.tei-c.org/ns/1.0"

"""
Base class for storing TEI XML witness data internally.
"""
class witness():
    """
    Constructs a new witness instance from the TEI XML input.
    """
    def __init__(self, xml, verbose=False):
        # If it has a type, then save that; otherwise, default to "manuscript":
        self.type = xml.get("type") if xml.get("type") is not None else "manuscript"
        # Use its xml:id if it has one; otherwise, use its n attribute if it has one; otherwise, use its text:
        self.id = ""
        if xml.get("{%s}id" % xml_ns) is not None:
            self.id = xml.get("{%s}id" % xml_ns)
        elif xml.get("n") is not None:
            self.id = xml.get("n")
        else:
            self.id = xml.text
        if verbose:
            print("New witness %s with type %s" % (self.id, self.type))

"""
Base class for storing TEI XML reading data internally.
This can correspond to a <lem>, <rdg>, or <witDetail> element in the collation.
"""
class reading():
    """
    Constructs a new reading instance from the TEI XML input.
    """
    def __init__(self, xml, verbose=False):
        # If it has a type, then save that; otherwise, default to "substantive":
        self.type = xml.get("type") if xml.get("type") is not None else "substantive"
        # Serialize its contents:
        self.text = self.serialize(xml)
        # Use its xml:id if it has one; otherwise, use its n attribute if it has one; otherwise, use its text:
        self.id = ""
        if xml.get("{%s}id" % xml_ns) is not None:
            self.id = xml.get("{%s}id" % xml_ns)
        elif xml.get("n") is not None:
            self.id = xml.get("n")
        else:
            self.id = xml.text
        # Save a list of the targets in its target attribute (stripping any "#" prefixes), split over spaces:
        self.targets = [t.strip("#") for t in xml.get("target").split()] if xml.get("target") is not None else []
        # Save a list of the entries in its wit attribute (stripping any "#" prefixes), split over spaces:
        self.wits = [w.strip("#") for w in xml.get("wit").split()] if xml.get("wit") is not None else []
        if verbose:
            if len(self.wits) == 0:
                if self.text != "":
                    print("New reading %s with type %s, no witnesses, and text %s" % (self.id, self.type, self.text))
                else:
                    print("New reading %s with type %s, no witnesses, and no text" % (self.id, self.type))
            else:
                if self.text != "":
                    print("New reading %s with type %s, witnesses %s, and text %s" % (self.id, self.type, ", ".join([wit for wit in self.wits]), self.text))
                else:
                    print("New reading %s with type %s, witnesses %s, and no text" % (self.id, self.type, ", ".join([wit for wit in self.wits])))

    """
    Given an XML element, recursively serializes it in a more readable format.
    """
    def serialize(self, xml):
        # Determine what this element is:
        raw_tag = xml.tag.replace("{%s}" % tei_ns, "")
        # If it is a reading, then serialize its children, separated by spaces:
        if raw_tag == "rdg":
            text = "" if xml.text is None else xml.text
            text += " ".join([self.serialize(child) for child in xml])
            return text
        # If it is a word, abbreviation, or overline-rendered element, then serialize its text and tail, 
        # recursively processing any subelements:
        if raw_tag in ["w", "abbr"]:
            text = "" if xml.text is None else xml.text
            text += "".join([self.serialize(child) for child in xml])
            text += "" if xml.tail is None else xml.tail
            return text
        # If it is an overline-rendered element, then add an overline to each character in its contents:
        if raw_tag == "hi":
            text = ""
            text += "" if xml.text is None else xml.text
            text += " ".join([self.serialize(child) for child in xml])
            # NOTE: other rendering types could be supported here
            if xml.get("rend") is not None:
                rend = xml.get("rend")
                if rend == "overline":
                    text = "".join([c + "\u0305" for c in text])
            text += "" if xml.tail is None else xml.tail
            return text
        # If it is a space, then serialize as a single space:
        if raw_tag == "space":
            text = "["
            if xml.get("unit") is not None and xml.get("extent") is not None:
                text += ", "
                unit = xml.get("unit")
                extent = xml.get("extent")
                text += extent + " " + unit
                text += " "
                text += "space"
            else:
                text += "space"
            if xml.get("reason") is not None:
                text += " "
                reason = xml.get("reason")
                text += "(" + reason + ")"
            text += "]"
            text += "" if xml.tail is None else xml.tail
            return text
        # If it is an expansion, then serialize it in parentheses:
        if raw_tag == "ex":
            text = ""
            text += "("
            text += "" if xml.text is None else xml.text
            text += " ".join([self.serialize(child) for child in xml])
            text += ")"
            text += "" if xml.tail is None else xml.tail
            return text
        # If it is a gap, then serialize it based on its attributes:
        if raw_tag == "gap":
            text = ""
            text += "["
            if xml.get("unit") is not None and xml.get("extent") is not None:
                unit = xml.get("unit")
                extent = xml.get("extent")
                text += extent + " " + unit
                text += " "
                text += "gap"
            else:
                text += "..." # placeholder text for gap if no unit and extent are specified
            if xml.get("reason") is not None:
                text += " "
                reason = xml.get("reason")
                text += "(" + reason + ")"
            text += "]"
            text += "" if xml.tail is None else xml.tail
            return text
        # If it is a supplied element, then recursively set the contents in brackets:
        if raw_tag == "supplied":
            text = ""
            text += "["
            text += "" if xml.text is None else xml.text
            text += " ".join([self.serialize(child) for child in xml])
            text += "]"
            text += "" if xml.tail is None else xml.tail
            return text
        # If it is an unclear element, then add an underdot to each character in its contents:
        if raw_tag == "unclear":
            text = ""
            text += "" if xml.text is None else xml.text
            text += " ".join([self.serialize(child) for child in xml])
            text = "".join([c + "\u0323" for c in text])
            text += "" if xml.tail is None else xml.tail
            return text
        # If it is a choice element, then recursively set the contents in brackets, separated by slashes:
        if raw_tag == "choice":
            text = ""
            text += "["
            text += "" if xml.text is None else xml.text
            text += "/".join([self.serialize(child) for child in xml])
            text += "]"
            text += "" if xml.tail is None else xml.tail
            return text
        # If it is a ref element, then set its text in brackets:
        if raw_tag == "ref":
            text = ""
            text += "["
            text += "" if xml.text is None else xml.text
            text += "]"
            text += "" if xml.tail is None else xml.tail
            return text
        # For all other elements, return an empty string:
        return ""

"""
Base class for storing TEI XML variation unit data internally.
"""
class variation_unit():
    """
    Constructs a new variation_unit instance from the TEI XML input.
    """
    def __init__(self, xml, verbose=False):
        # If it has a type, then save that; otherwise, default to "substantive":
        self.type = xml.get("type") if xml.get("type") is not None else "substantive"
        # Use its xml:id if it has one; otherwise, use its n attribute if it has one:
        self.id = ""
        if xml.get("{%s}id" % xml_ns) is not None:
            self.id = xml.get("{%s}id" % xml_ns)
        elif xml.get("n") is not None:
            self.id = xml.get("n")
        # Initialize its list of readings:
        self.readings = []
        # Now parse the XML <app> element to populate these data structures:
        self.parse(xml, verbose)
        if verbose:
            print("New variation_unit %s of type %s with %d readings" % (self.id, self.type, len(self.readings)))

    """
    Given an XML element, recursively parses its subelements for readings and reading groups.
    Other children of <app> elements, such as <note>, <noteGrp>, and <wit> elements, are ignored.
    """
    def parse(self, xml, verbose):
        # Determine what this element is:
        raw_tag = xml.tag.replace("{%s}" % tei_ns, "")
        # If it is an apparatus, then initialize the readings list and process the child elements of the apparatus recursively:
        if raw_tag == "app":
            self.readings = []
            for child in xml:
                self.parse(child, verbose)
            return
        # If it is a reading group, then flatten it by processing its children recursively, applying the reading group's type to the readings contained in it:
        if raw_tag == "rdgGrp":
            # Get the type of this reading group:
            reading_group_type = xml.get("type") if xml.get("type") is not None else None
            for child in xml:
                child_raw_tag = child.tag.replace("{%s}" % tei_ns, "")
                if child_raw_tag in ["lem", "rdg"]: # any <lem> element in a <rdgGrp> can be assumed not to be a duplicate of a <rdg> element, as there should be only one <lem> at all levels under an <app> element
                    rdg = reading(child, verbose)
                    if rdg.type is not None:
                        rdg.type = reading_group_type
                    self.readings.append(rdg)
                else:
                    self.parse(child, verbose)
            return
        # If it is a lemma, then add it as a reading if has its own witness list (even if that list is empty, which may occur for a conjecture);
        # otherwise, assume its reading is duplicated in a <rdg> element and skip it:
        if raw_tag == "lem":
            if xml.get("wit") is not None:
                lem = reading(xml, verbose)
                self.readings.append(lem)
            return
        # If it is a reading, then add it as a reading:
        elif raw_tag == "rdg":
            rdg = reading(xml, verbose)
            self.readings.append(rdg)
            return
        # If it is a witness detail, then add it as a reading, and if it does not have any targeted readings, then add a target for the previous reading (per the TEI Guidelines §12.1.4.1):
        elif raw_tag == "witDetail":
            witDetail = reading(xml, verbose)
            if len(witDetail.targets) == 0 and len(self.readings) > 0:
                previous_rdg = self.readings[-1]
                witDetail.targets.append(previous_rdg.id)
            self.readings.append(witDetail)
            return

"""
Base class for storing TEI XML collation data internally.
"""
class collation():
    """
    Constructs a new collation instance with the given settings.
    """
    def __init__(self, xml, manuscript_suffixes=[], trivial_reading_types=[], missing_reading_types=[], fill_corrector_lacunae=False, verbose=False):
        self.manuscript_suffixes = manuscript_suffixes # list of suffixes used to distinguish manuscript subwitnesses like first hands, correctors, main texts, alternate texts, and multiple attestations from their base witnesses
        self.trivial_reading_types = set(trivial_reading_types) # set of reading types (e.g., defective, orthographic, subreading) whose readings should be collapsed under the previous substantive reading
        self.missing_reading_types = set(missing_reading_types) # set of reading types (e.g., lacunose, overlap) whose readings should be treated as missing data
        self.fill_corrector_lacunae = fill_corrector_lacunae # flag indicating whether or not to fill "lacuna" in witnesses with type "corrector"
        self.verbose = verbose # flag indicating whether or not to print timing and debugging details for the user
        self.witnesses = [] # a list of witness instances
        self.witness_index_by_id = {} # a dictionary mapping base witness IDs to their indices in the above list
        self.variation_units = [] # a list of variation_unit instances
        self.readings_by_witness = {} # a dictionary mapping base witness IDs to a list of reading support sets for all units (with at least two substantive readings)
        self.substantive_variation_unit_ids = [] # a list of IDs for variation units with two or more substantive readings
        # Now parse the XML tree to populate these data structures:
        if self.verbose:
            print("Initializing collation...")
        t0 = time.time()
        self.parse_list_wit(xml, verbose)
        self.parse_apps(xml, verbose)
        self.parse_readings_by_witness(verbose)
        t1 = time.time()
        if self.verbose:
            print("Total time to initialize collation: %0.4fs." % (t1 - t0))

    """
    Given an XML tree for a collation, populates its list of witnesses from its <listWit> element.
    """
    def parse_list_wit(self, xml, verbose=False):
        if self.verbose:
            print("Parsing witness list...")
        t0 = time.time()
        self.witnesses = []
        self.witness_index_by_id = {}
        for w in xml.xpath("/tei:TEI/tei:teiHeader/tei:fileDesc/tei:sourceDesc/tei:listWit/tei:witness", namespaces={"tei": tei_ns}):
            wit = witness(w, verbose)
            self.witness_index_by_id[wit.id] = len(self.witnesses)
            self.witnesses.append(wit)
        t1 = time.time()
        if verbose:
            print("Finished processing %d witnesses in %0.4fs." % (len(self.witnesses), t1 - t0))
        return

    """
    Given an XML tree for a collation, populates its list of variation units from its <app> elements.
    """
    def parse_apps(self, xml, verbose=False):
        if self.verbose:
            print("Parsing variation units...")
        t0 = time.time()
        for a in xml.xpath('//tei:app', namespaces={'tei': tei_ns}):
            vu = variation_unit(a, verbose)
            self.variation_units.append(vu)
        t1 = time.time()
        if verbose:
            print("Finished processing %d variation units in %0.4fs." % (len(self.variation_units), t1 - t0))
        return

    """
    Given a witness siglum, strips of the specified manuscript suffixes 
    until the siglum matches one in the witness list or until no more suffixes can be stripped.
    """
    def get_base_wit(self, wit):
        base_wit = wit
        # If our starting siglum corresponds to a siglum in the witness list, then just return it:
        if base_wit in self.witness_index_by_id:
            return base_wit
        # Otherwise, strip any suffixes we find until the siglum corresponds to a base witness in the list
        # or no more suffixes can be stripped:
        suffix_found = True
        while (suffix_found):
            suffix_found = False
            for suffix in self.manuscript_suffixes:
                if base_wit.endswith(suffix):
                    suffix_found = True
                    base_wit = base_wit[:-len(suffix)]
                    break # stop looking for other suffixes
            # If the siglum stripped of this suffix now corresponds to a siglum in the witness list, then return it:
            if base_wit in self.witness_index_by_id:
                return base_wit
        # If we get here, then all possible manuscript suffixes have been stripped, and the resulting siglum does not correspond to a siglum in the witness list:
        return base_wit

    """
    Returns a dictionary mapping witness IDs to a set of their readings for a given variation unit.
    """
    def get_readings_by_witness_for_unit(self, vu, verbose=False):
        # In a first pass, populate a list of substantive readings and a map from reading IDs to the indices of their parent substantive reading in this unit:
        substantive_reading_ids = []
        reading_id_to_index = {}
        for rdg in vu.readings:
            # If this reading is missing (e.g., lacunose or inapplicable due to an overlapping variant) or targets another reading, then skip it:
            if rdg.type in self.missing_reading_types or len(rdg.targets) > 0:
                continue
            # If this reading is trivial, then map it to the last substantive index:
            if rdg.type in self.trivial_reading_types:
                reading_id_to_index[rdg.id] = len(substantive_reading_ids) - 1
                continue
            # Otherwise, the reading is substantive: add it to the map and update the last substantive index:
            substantive_reading_ids.append(rdg.id)
            reading_id_to_index[rdg.id] = len(substantive_reading_ids) - 1
        # If the list of substantive readings only contains one entry, then this variation unit is not informative;
        # return an empty dictionary:
        if self.verbose:
            print("Variation unit %s has %d substantive readings." % (vu.id, len(substantive_reading_ids)))
        readings_by_witness_for_unit = {}
        if len(substantive_reading_ids) <= 1:
            return readings_by_witness_for_unit
        # Otherwise, initialize the output dictionary with empty sets for all base witnesses:
        for wit in self.witnesses:
            readings_by_witness_for_unit[wit.id] = [0]*len(substantive_reading_ids)
        # In a second pass, assign each base witness a set containing the readings it supports in this unit:
        for rdg in vu.readings:
            # Initialize the dictionary indicating support for this reading (or its disambiguations):
            rdg_support = [0]*len(substantive_reading_ids)
            # If this is a missing reading (e.g., a lacuna or an overlap), then we can skip this reading, as its corresponding set will be empty:
            if rdg.type in self.missing_reading_types:
                continue
            # If this reading is trivial, then it will contain an entry for the index of its parent substantive reading:
            if rdg.type in self.trivial_reading_types:
                rdg_support[reading_id_to_index[rdg.id]] += 1
            # Otherwise, if this reading has one or more target readings, then add an entry for the index of each of those readings:
            elif len(rdg.targets) > 0:
                for t in rdg.targets:
                    # TODO: If the reading has certainty values assigned to these values, then use these rather than 1
                    rdg_support[reading_id_to_index[t]] += 1
            # Otherwise, this reading is itself substantive; add an entry for the index of this reading:
            else:
                rdg_support[reading_id_to_index[rdg.id]] += 1
            # Proceed for each witness siglum in the support for this reading:
            for wit in rdg.wits:
                # Is this siglum a base siglum?
                base_wit = self.get_base_wit(wit)
                if base_wit not in self.witness_index_by_id:
                    # If it is not, then it is probably just because we've encountered a corrector or some other secondary witness not included in the witness list;
                    # report this if we're in verbose mode and move on:
                    if verbose:
                        print("Skipping unknown witness siglum %s (base siglum %s) in variation unit %s, reading %s..." % (wit, base_wit, vu.id, rdg.id))
                    continue
                # If we've found a base siglum, then add this reading's contribution to the base witness's reading set for this unit;
                # normally the existing set will be empty, but if we reduce two suffixed sigla to the same base witness, 
                # then that witness may attest to multiple readings in the same unit:
                readings_by_witness_for_unit[base_wit] = [(readings_by_witness_for_unit[base_wit][i] + rdg_support[i]) for i in range(len(rdg_support))]
        # In a third pass, normalize the reading weights for all non-lacunose readings:
        for wit in readings_by_witness_for_unit:
            rdg_support = readings_by_witness_for_unit[wit]
            norm = sum(rdg_support)
            # Skip lacunae, as we can't normalize the vector of reading weights:
            if norm == 0:
                continue
            for i in range(len(rdg_support)):
                rdg_support[i] = rdg_support[i]/norm
        return readings_by_witness_for_unit

    """
    Populates the internal dictionary mapping witness IDs to a list of their reading support sets for all variation units,
    and then fills the empty reading support sets for witnesses of type "corrector" with the entries of the previous witness.
    """
    def parse_readings_by_witness(self, verbose=False):
        if self.verbose:
            print("Populating internal dictionary of witness readings...")
        t0 = time.time()
        # Initialize the data structures to be populated here:
        self.readings_by_witness = {}
        self.substantive_variation_unit_ids = []
        for wit in self.witnesses:
            self.readings_by_witness[wit.id] = []
        # Populate them for each variation unit:
        for vu in self.variation_units:
            readings_by_witness_for_unit = self.get_readings_by_witness_for_unit(vu, verbose)
            if len(readings_by_witness_for_unit) > 0:
                self.substantive_variation_unit_ids.append(vu.id)
            for wit in readings_by_witness_for_unit:
                self.readings_by_witness[wit].append(readings_by_witness_for_unit[wit])
        # Optionally, fill the lacunae of the correctors:
        if self.fill_corrector_lacunae:
            for i, wit in enumerate(self.witnesses):
                # If this is the first witness, then it shouldn't be a corrector (since there is no previous witness against which to compare it):
                if i == 0:
                    continue
                # Otherwise, if this witness is not a corrector, then skip it:
                if wit.type != "corrector":
                    continue
                # Otherwise, retrieve the previous witness:
                prev_wit = self.witnesses[i-1]
                for j in range(len(self.readings_by_witness[wit.id])):
                    # If the corrector has no reading, then set it to the previous witness's reading:
                    if sum(self.readings_by_witness[wit.id][j]) == 0:
                        self.readings_by_witness[wit.id][j] = self.readings_by_witness[prev_wit.id][j]
        t1 = time.time()
        if verbose:
            print("Populated dictionary for %d witnesses over %d substantive variation units in %0.4fs." % (len(self.witnesses), len(self.substantive_variation_unit_ids), t1 - t0))
        return

    """
    Returns a list of one-character symbols needed to represent the states of all substantive readings in NEXUS.
    """
    def get_nexus_symbols(self):
        possible_symbols = list(string.digits) + list(string.ascii_letters)
        # The number of symbols needed is equal to the length of the longest substantive reading vector:
        nsymbols = 0
        # If there are no witnesses, then no symbols are needed at all:
        if len(self.witnesses) == 0:
            return []
        wit_id = self.witnesses[0].id
        for rdg_support in self.readings_by_witness[wit_id]:
            nsymbols = max(nsymbols, len(rdg_support))
        nexus_symbols = possible_symbols[:nsymbols]
        return nexus_symbols

    """
    Writes this collation to a NEXUS file with the given address.
    """
    def to_nexus(self, file_addr):
        # Start by calculating the values we will be using here:
        ntax = len(self.witnesses)
        nchar = len(self.readings_by_witness[self.witnesses[0].id]) if ntax > 0 else 0 # if the number of taxa is 0, then the number of characters is irrelevant
        taxlabels = [wit.id for wit in self.witnesses]
        charlabels = self.substantive_variation_unit_ids
        missing_symbol = '?'
        symbols = self.get_nexus_symbols()
        with open(file_addr, "w", encoding="utf-8") as f:
            # Start with the NEXUS header:
            f.write("#NEXUS\n\n")
            # Then begin the taxa block:
            f.write("Begin TAXA;\n")
            # Write the number of taxa:
            f.write("\tDimensions ntax=%d;\n" % (ntax))
            # Write the labels for taxa, separated by spaces:
            f.write("\tTaxLabels %s;\n" % (" ".join(taxlabels)))
            # End the taxa block:
            f.write("End;\n\n")
            # Then begin the characters block:
            f.write("Begin CHARACTERS;\n")
            # Write the number of characters:
            f.write("\tDimensions nchar=%d;\n" % (nchar))
            # Write the labels for characters, with each on its own line:
            f.write("\tCharLabels\n\t\t%s;\n" % ("\n\t\t".join(charlabels)))
            # Write the format subblock:
            f.write("\tFormat\n\t\tDataType=Standard\n\t\tStatesFormat=Frequency\n\t\tSymbols=\"%s\";\n" % (" ".join(symbols)))
            # Write the matrix subblock:
            f.write("\tMatrix")
            for i, wit in enumerate(self.witnesses):
                taxlabel = wit.id
                sequence = "\n\t\t" + taxlabel
                for rdg_support in self.readings_by_witness[wit.id]:
                    sequence += "\n\t\t\t"
                    # If this reading is lacunose in this witness, then use the missing character:
                    if sum(rdg_support) == 0:
                        sequence += missing_symbol
                        continue
                    # Otherwise, print out its frequencies for different readings in parentheses:
                    sequence += "("
                    for j, w in enumerate(rdg_support):
                        sequence += "%s:%0.4f" % (symbols[j], w)
                        if j < len(rdg_support) - 1:
                            sequence += " "
                    sequence += ")"
                f.write("%s" % (sequence))
            f.write(";\n")
            # End the characters block:
            f.write("End;")
        return

    # TODO: Add output methods for CSV, Excel, and, if possible, Stemma