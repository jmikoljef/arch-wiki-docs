#! /usr/bin/env python

import os
import lxml.etree
import lxml.html
import urllib.request

class ArchWikiOptimizer:
    def __init__(self, base_directory):
        """ @base_directory: absolute path to base output directory, used for
                             computation of relative links
        """

        self.base_directory = base_directory 

    def optimize(self, url, fout):
        """ @url: input url path for lxml
            @fout: output file name (must be absolute path)
        """

        # path relative from the HTML file to base output directory
        self.relbase = os.path.relpath(self.base_directory, os.path.split(fout)[0])

        # parse HTML into element tree
        self.tree = lxml.html.parse(urllib.request.urlopen(url))
        self.root = self.tree.getroot()

        # optimize
        self.strip_page()
        self.fix_layout()
        self.replace_css_links()
        self.update_links()
        self.fix_footer()

        # ensure that target directory exists (necessary for subpages)
        try:
            os.makedirs(os.path.split(fout)[0])
        except FileExistsError:
            pass

        # write output
        f = open(fout, "w")
        f.write(lxml.etree.tostring(self.root,
                                    pretty_print=True,
                                    encoding="unicode",
                                    method="html",
                                    doctype="<!DOCTYPE html>"))
        f.close()

    def strip_page(self):
        """ remove elements useless in offline browsing
        """

        for e in self.root.cssselect("#archnavbar, #column-one, span.mw-editsection, #jump-to-nav, #siteSub"):
            e.getparent().remove(e)

        # strip comments (including IE 6/7 fixes, which are useless for an Arch package)
        lxml.etree.strip_elements(self.root, lxml.etree.Comment)

    def fix_layout(self):
        """ fix page layout after removing some elements
        """

        gw = self.root.cssselect("#globalWrapper")[0]
        gw.set("style", "width: 100%")
        c = self.root.cssselect("#content")[0]
        c.set("style", "margin: 2em; margin-bottom: 0")
        fl = self.root.cssselect("#f-list")[0]
        fl.set("style", "margin: 0 2em")

    def replace_css_links(self):
        """ force using local CSS
        """

        links = self.root.xpath("//head/link[@rel=\"stylesheet\"]")

        # FIXME: pass css fille name as parameter
        # overwrite first
        links[0].set("href", os.path.join(self.relbase, "ArchWikiOffline.css"))
        
        # remove the rest
        for link in links[1:]:
            link.getparent().remove(link)

    def update_links(self):
        """ change "internal" wiki links into relative
        """

        for a in self.root.cssselect("a"):
            href = a.get("href")
            if href and href.startswith("/index.php/"):
                # make relative
                href = href.replace("/index.php", self.relbase)

                # if not from the 'File' namespace, add the '.html' suffix
                if not href.startswith("./File:"):
                    # links to sections
                    if "#" in href:
                        href = href.replace("#", ".html#")
                    else:
                        href += ".html"

                a.set("href", href)

        for i in self.root.cssselect("img"):
            src = i.get("src")
            if src and src.startswith("/images/"):
                src = os.path.join(self.relbase, "File:" + os.path.split(src)[1])
                i.set("src", src)

    def fix_footer(self):
        """ move content from 'div.printfooter' into item in '#f-list'
            (normally 'div#printfooter' is given 'display:none' and is separated by
            the categories list from the real footer)
        """

        printfooter = self.root.cssselect("div.printfooter")[0]
        printfooter.attrib.pop("class")
        printfooter.tag = "li"
        f_list = self.root.cssselect("#f-list")[0]
        f_list.insert(0, printfooter)
        br = lxml.etree.Element("br")
        f_list.insert(3, br)

if __name__ == "__main__":
    awoo = ArchWikiOptimizer("./wiki")
#    awoo.optimize("testing_input.html", "./testing_output.html")
    awoo.optimize("https://wiki.archlinux.org/index.php/Systemd", "./testing_output.html")
