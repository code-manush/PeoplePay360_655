export function numberToWords(num: number): string {
    if (num === 0) return 'Zero';
    
    const a = ['', 'One ', 'Two ', 'Three ', 'Four ', 'Five ', 'Six ', 'Seven ', 'Eight ', 'Nine ', 'Ten ', 'Eleven ', 'Twelve ', 'Thirteen ', 'Fourteen ', 'Fifteen ', 'Sixteen ', 'Seventeen ', 'Eighteen ', 'Nineteen '];
    const b = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety'];
  
    const formatChunk = (n: number) => {
        if (n === 0) return '';
        let str = '';
        if (n > 99) {
            str += a[Math.floor(n / 100)] + 'Hundred ';
            n = n % 100;
        }
        if (n > 19) {
            str += b[Math.floor(n / 10)] + (n % 10 ? '-' + a[n % 10] : ' ');
        } else {
            str += a[n];
        }
        return str;
    };
  
    let result = '';
    const wholeNumber = Math.floor(num);
    let n = wholeNumber;
    
    if (n >= 10000000) {
        result += formatChunk(Math.floor(n / 10000000)) + 'Crore ';
        n %= 10000000;
    }
    if (n >= 100000) {
        result += formatChunk(Math.floor(n / 100000)) + 'Lakh ';
        n %= 100000;
    }
    if (n >= 1000) {
        result += formatChunk(Math.floor(n / 1000)) + 'Thousand ';
        n %= 1000;
    }
    if (n > 0) {
        result += formatChunk(n);
    }
    
    return result.trim();
}
