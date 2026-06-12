
import {Fragment,memo,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {Box as RadixThemesBox,Flex as RadixThemesFlex,Text as RadixThemesText} from "@radix-ui/themes"
import {jsx} from "@emotion/react"






export const Foreach_comp_a922e3bbc22c31a0321dd4ad934c1365 = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)
const [addEvents, connectErrors] = useContext(EventLoopContext);



    return(
        Array.prototype.map.call(reflex___state____state__cura___state____app_state.wi_grid_rows_rx_state_ ?? [],((row_rx_state_,index_c250ed0f7f5aadf8797bcb2a8d21c467)=>(jsx("tr",{css:({ ["borderBottom"] : "1px solid rgba(255,255,255,0.08)33", ["&:hover"] : ({ ["background"] : "rgba(255,255,255,0.015)" }) }),key:index_c250ed0f7f5aadf8797bcb2a8d21c467},jsx("td",{css:({ ["position"] : "sticky", ["left"] : "0", ["zIndex"] : "5", ["background"] : "#0C0C10", ["borderRight"] : "1px solid rgba(255,255,255,0.14)", ["minWidth"] : "160px", ["maxWidth"] : "160px", ["padding"] : "0 10px", ["height"] : "38px", ["whiteSpace"] : "nowrap", ["overflow"] : "hidden", ["textOverflow"] : "ellipsis", ["verticalAlign"] : "middle" })},jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["gap"] : "6px", ["alignItems"] : "center", ["width"] : "100%" }),direction:"row",gap:"3"},jsx(RadixThemesBox,{css:({ ["width"] : "8px", ["height"] : "8px", ["borderRadius"] : "50%", ["background"] : row_rx_state_?.["cat_color"], ["flexShrink"] : "0" })},),jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "12px", ["color"] : "#FFFFFF", ["whiteSpace"] : "nowrap", ["overflow"] : "hidden", ["textOverflow"] : "ellipsis" })},row_rx_state_?.["name"]))),Array.prototype.map.call(row_rx_state_?.["cells"] ?? [],((cell_rx_state_,index_875c31822ae819eb6ab9f8e2a70261aa)=>(jsx("td",{css:({ ["minWidth"] : "100px", ["maxWidth"] : "120px", ["height"] : "38px", ["padding"] : "0 10px", ["cursor"] : "pointer", ["textAlign"] : "right", ["verticalAlign"] : "middle", ["whiteSpace"] : "nowrap", ["borderRight"] : "1px solid rgba(255,255,255,0.08)", ["background"] : ((cell_rx_state_?.["tx_class"]?.valueOf?.() === "off"?.valueOf?.()) ? "rgba(255,69,58,0.06)" : ((cell_rx_state_?.["tx_class"]?.valueOf?.() === "start"?.valueOf?.()) ? "rgba(48,209,88,0.08)" : ((cell_rx_state_?.["tx_class"]?.valueOf?.() === "chg"?.valueOf?.()) ? "rgba(255,159,10,0.06)" : "transparent"))), ["borderLeft"] : ((cell_rx_state_?.["tx_class"]?.valueOf?.() === "off"?.valueOf?.()) ? "3px solid rgba(255,69,58,0.4)" : ((cell_rx_state_?.["tx_class"]?.valueOf?.() === "start"?.valueOf?.()) ? "3px solid rgba(48,209,88,0.5)" : ((cell_rx_state_?.["tx_class"]?.valueOf?.() === "chg"?.valueOf?.()) ? "3px solid rgba(255,159,10,0.5)" : "3px solid transparent"))), ["&:hover"] : ({ ["background"] : "rgba(191,90,242,0.08)" }) }),key:index_875c31822ae819eb6ab9f8e2a70261aa,onClick:((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.open_cell_pop", ({ ["bid"] : cell_rx_state_?.["bid"], ["mkey"] : cell_rx_state_?.["mkey"] }), ({  })))], [_e], ({  }))))},jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "12px", ["fontFamily"] : "'JetBrains Mono', monospace", ["--default-font-family"] : "'JetBrains Mono', monospace", ["fontWeight"] : "500", ["color"] : ((cell_rx_state_?.["tx_class"]?.valueOf?.() === "off"?.valueOf?.()) ? "#606088" : ((cell_rx_state_?.["tx_class"]?.valueOf?.() === "start"?.valueOf?.()) ? "#30D158" : ((cell_rx_state_?.["tx_class"]?.valueOf?.() === "chg"?.valueOf?.()) ? "#FF9F0A" : "#9090B8"))), ["textDecoration"] : ((cell_rx_state_?.["tx_class"]?.valueOf?.() === "off"?.valueOf?.()) ? "line-through" : "none") })},cell_rx_state_?.["amount_fmt"])))))))))
    )
});
