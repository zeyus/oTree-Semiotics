/**
     * A class that takes care of drawing on the canvas
     * @field
     */
class Drawer {
    #SVGElement;
    #rect;

    #buffer = [];
    #bufferSize = 8; // Change to decrease/increase smoothness of paths

    #path = null;
    #strPath;
    #userPaths = [];

    #pathColor = "#cb1212"; // Edit this to change the drawing color
    #pathStrokeWidth = "15"; // Edit this to change the stroke width
    #pathStrokeEnds = "round"; // Edit this to change the stroke ends

    /**
     * The SVG element that needs
     * @param {HTMLElement} SVGElement An SVG element to draw in
     */
    constructor(SVGElement) {
        this.#SVGElement = SVGElement;
        this.#rect = SVGElement.getBoundingClientRect();
    }

    /**
     * A handler function for 'mousedown';
     * @param {MouseEvent} e The event object
     */
    startDraw(e) {
        this.#path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        this.#path.setAttribute("fill", "none");
        this.#path.setAttribute("stroke", this.#pathColor);
        this.#path.setAttribute("stroke-width", this.#pathStrokeWidth);
        this.#path.setAttribute("stroke-linecap", this.#pathStrokeEnds);
        this.#buffer = [];
        let pt = this.#getMousePosition(e);
        this.#appendToBuffer(pt);
        this.#strPath = "M" + pt.x + " " + pt.y;
        this.#path.setAttribute("d", this.#strPath);
        this.#path.setAttribute("data-is-user", "true")
        this.#SVGElement.appendChild(this.#path);
    }

    /**
     * A handler function for 'mousemove'
     * @param {MouseEvent} e The event object
     */
    draw(e) {
        if (this.#path) {
            this.#appendToBuffer(this.#getMousePosition(e));
            this.#updateSvgPath();
        }
    }

    /**
     * A handler function for 'mouseup'
     */
    stopDraw() {
        if (this.#path) {
            this.#userPaths.push(this.#path)
            this.#path = null;
        }
    }

    /**
     * A handler function that forces the drawing until event position ('mouseleave')
     * @param {MouseEvent} e The event object
     */
    stopDrawAndForceToEnd(e) {
        this.draw(e);
        this.stopDraw();
    }

    /**
     * Removes the last path drawn on the SVG
     */
    undoAction() {
        if (this.#userPaths.length === 0) {
            return;
        }
        this.#userPaths.pop().remove();
    }

    /**
     * Restores a list of userPaths to the SVG
     */
    restorePaths(userPaths) {
        this.#userPaths = [];
        for (let p of userPaths) {
            this.#SVGElement.appendChild(p);
            this.#userPaths.push(p);
        }
    }

    /**
     * Removes all user-drawn paths from the SVG
     */
    clearSVG() {
        for (let p of this.#userPaths) {
            p.remove();
        }
        this.#userPaths = [];
    }

    /**
     * Gets relative x- and y-position of mouse within SVG element
     * @param e
     * @return {{x: number, y: number}}
     */

    #getMousePosition(e) {
        return {
            x: e.pageX - this.#rect.left,
            y: e.pageY - this.#rect.top
        }
    }

    /**
     * Appends coordinate to buffer for drawing more fluently
     * @param {{x: number, y: number}} pt
     */
    #appendToBuffer(pt) {
        this.#buffer.push(pt);
        while (this.#buffer.length > this.#bufferSize) {
            this.#buffer.shift();
        }
    }

    /**
     * Gets an average of points from the buffer and appends to SVG path element
     */
    #updateSvgPath() {
        let pt = this.#getAveragePoint(0);

        if (pt) {
            // Get the smoothed part of the path that will not change
            this.#strPath += " L" + pt.x + " " + pt.y;

            // Get the last part of the path (close to the current mouse position)
            // This part will change if the mouse moves again
            let tmpPath = "";
            for (let offset = 2; offset < this.#buffer.length; offset += 2) {
                pt = this.#getAveragePoint(offset);
                tmpPath += " L" + pt.x + " " + pt.y;
            }

            // Set the complete current path coordinates
            this.#path.setAttribute("d", this.#strPath + tmpPath);
        }
    }

    /**
     * Gets an average point based on point buffer
     * @param {number} offset An offset in the buffer array
     * @return {null|{x: number, y: number}} Returns an average point or null (magic)
     */
    #getAveragePoint(offset) {
        const len = this.#buffer.length;
        if (len % 2 === 1 || len >= this.#bufferSize) {
            let totalX = 0;
            let totalY = 0;
            let pt, i;
            let count = 0;
            for (i = offset; i < len; i++) {
                count++;
                pt = this.#buffer[i];
                totalX += pt.x;
                totalY += pt.y;
            }
            return {
                x: totalX / count,
                y: totalY / count
            }
        }
        return null;
    }
}

/**
 * Helper class with various static functions, e.g., export and download
 */
class Helper {
    /**
     * Takes a blob object and transforms it into base64-encoded data URL
     * @param blob The blob to transform
     * @return {Promise<unknown>} Resolves to the base64-encoded string
     */
    static async #blobToBase64(blob) {
        // console.log(blob)
        return new Promise((resolve, _) => {
            const reader = new FileReader();
            reader.onloadend = () => resolve(reader.result);
            reader.readAsDataURL(blob);
        });
    }

    /**
     * Helper function to download arbitrary data (text, base64, etc.) from browser
     * @param {string} dataURL The data to save in a file
     * @param filename The default filename for the user to see
     */
    static #download(dataURL, filename) {
        const a = document.createElement('a');
        a.href = dataURL;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(dataURL)
        a.remove()
    }

    /**
     * Exports the SVG and downloads
     */
    static async exportSVG(asBase64 = false) {
        let svg = svgElement.outerHTML;
        let blob = new Blob([svg], {type: 'image/svg+xml'});
        if (!asBase64) {
            let url = URL.createObjectURL(blob);
            this.#download(url, 'new-drawing.svg');
        } else {
            let base64data = await this.#blobToBase64(blob);
            let properBase64data = base64data.substring(base64data.indexOf(',')+1);
            let base64RegExp = /^([0-9a-zA-Z+/]{4})*(([0-9a-zA-Z+/]{2}==)|([0-9a-zA-Z+/]{3}=))?$/;
            let isBase64 = base64RegExp.test(properBase64data);
            if (isBase64) {
                return properBase64data;
            } else {
                throw new Error("Something went wrong in converting to Base64")
            }
        }

    }

    /**
     * Import Base64-encoded SVG and append to the SVG element
     */
    static async importSVG(drawer, base64String) {
        const parser = new DOMParser();
        const svg = atob(base64String);
        // get all <path> elements from the SVG
        const doc = parser.parseFromString(svg, 'image/svg+xml');
        const paths = doc.querySelectorAll('path');
        drawer.restorePaths(paths);
    }

    /**
     * Exports the SVG to base64 and sends a HTTP request
     * @return {Promise<void>}
     */
    static async sendSVG() {
        let base64String = await this.exportSVG(true);
        console.log(base64String);
        // Do stuff here to send using fetch
    }

    /**
     * Exports to PNG and downloads
     * @return {Promise<void>}
     */
    static async exportPNG() {
        const serializeAsXML = el => (new XMLSerializer()).serializeToString(el);
        const encodeAsUTF8 = serializedString => `${dataHeader},${encodeURIComponent(serializedString)}`

        /**
         * A helper function
         * @param {string} url A data URL
         * @return {Promise<HTMLImageElement>} A promise that resolves to an IMG element
         */
        const loadImage = async url => {
            const img = document.createElement('img');
            img.src = url;
            img.style.display = 'none';
            return new Promise((resolve, reject) => {
                img.onload = () => resolve(img)
                img.onerror = reject
                img.src = url
            })
        }

        const dataHeader = 'data:image/svg+xml;charset=utf-8';
        const format = 'png';
        const svgData = encodeAsUTF8(serializeAsXML(SVGelement));
        const img = await loadImage(svgData)

        const canvas = document.createElement('canvas');
        canvas.style.display = 'none';
        canvas.width = SVGelement.clientWidth;
        canvas.height = SVGelement.clientHeight;
        canvas.getContext('2d').drawImage(img, 0, 0, SVGelement.clientWidth, SVGelement.clientHeight)

        const dataURL = canvas.toDataURL(`image/${format}`, 1.0)
        console.log(dataURL)

        let download = document.createElement('a');
        download.href = dataURL;
        download.download = 'new-drawing.png';
        download.click();
        download.remove()
    }
}