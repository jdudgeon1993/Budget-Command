
import {Fragment,memo,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {Box as RadixThemesBox,Flex as RadixThemesFlex,Text as RadixThemesText} from "@radix-ui/themes"
import {jsx} from "@emotion/react"






export const Foreach_comp_82192ecd730c43525c08b47f10b7ec00 = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)
const [addEvents, connectErrors] = useContext(EventLoopContext);



    return(
        Array.prototype.map.call(reflex___state____state__cura___state____app_state.paycheck_rows_rx_state_ ?? [],((row_rx_state_,index_777536f7e3220d7b6e9271aedf13738b)=>(jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["background"] : "rgba(255,255,255,0.05)", ["border"] : "1px solid rgba(255,255,255,0.08)", ["borderRadius"] : "8px", ["padding"] : "10px 12px", ["marginBottom"] : "5px", ["alignItems"] : "center", ["width"] : "100%", ["gap"] : "8px" }),direction:"row",key:index_777536f7e3220d7b6e9271aedf13738b,gap:"3"},jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["gap"] : "1px", ["alignItems"] : "flex-start", ["flex"] : "1" }),direction:"column",gap:"3"},jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "13px", ["color"] : "#FFFFFF", ["fontWeight"] : "600" })},row_rx_state_?.["label"]),jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "12px", ["color"] : "#606088", ["fontFamily"] : "'JetBrains Mono', monospace", ["--default-font-family"] : "'JetBrains Mono', monospace" })},row_rx_state_?.["freq_label"])),jsx(RadixThemesText,{as:"p",css:({ ["fontFamily"] : "'JetBrains Mono', monospace", ["--default-font-family"] : "'JetBrains Mono', monospace", ["fontSize"] : "14px", ["fontWeight"] : "700", ["color"] : "#30D158", ["whiteSpace"] : "nowrap" })},row_rx_state_?.["amount_fmt"]),jsx(RadixThemesBox,{css:({ ["fontSize"] : "11px", ["color"] : "#BF5AF2", ["cursor"] : "pointer", ["padding"] : "3px 8px", ["borderRadius"] : "4px", ["border"] : "1px solid #BF5AF244", ["&:hover"] : ({ ["background"] : "#BF5AF211" }), ["fontFamily"] : "'JetBrains Mono', monospace", ["--default-font-family"] : "'JetBrains Mono', monospace", ["flexShrink"] : "0" }),onClick:((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.open_edit_paycheck", ({ ["pc_id"] : row_rx_state_?.["id"] }), ({  })))], [_e], ({  }))))},"Edit"),jsx(RadixThemesBox,{css:({ ["fontSize"] : "14px", ["color"] : "#606088", ["cursor"] : "pointer", ["padding"] : "2px 6px", ["borderRadius"] : "4px", ["&:hover"] : ({ ["color"] : "#FF453A", ["background"] : "#FF453A11" }) }),onClick:((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.delete_paycheck_item", ({ ["pc_id"] : row_rx_state_?.["id"] }), ({  })))], [_e], ({  }))))},"\u2715")))))
    )
});
